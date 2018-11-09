import ast
import astor
import inspect
import magma as m
import magma
import os
import sys
import logging
import functools
import operator

# logging.basicConfig(level=logging.DEBUG)

import silica
from silica.coroutine import Coroutine
from silica.cfg import ControlFlowGraph, BasicBlock, HeadBlock
from silica.cfg.control_flow_graph import render_paths_between_yields, build_state_info, render_fsm, get_constant
import silica.ast_utils as ast_utils
from silica.transformations import specialize_constants, replace_symbols, \
    constant_fold, desugar_for_loops, specialize_evals, inline_yield_from_functions
from silica.visitors import collect_names
import silica.verilog as verilog
from .memory import MemoryType
from silica.transformations.specialize_arguments import specialize_arguments
from silica.type_check import TypeChecker
from silica.analysis import CollectInitialWidthsAndTypes
from silica.transformations.promote_widths import PromoteWidths
from silica.transformations.desugar_for_loops import propagate_types, get_final_widths

import veriloggen as vg

def specialize_list_comps(tree, globals, locals):
    locals.update(silica.operators)
    class ListCompSpecializer(ast.NodeTransformer):
        def visit_ListComp(self, node):
            result = eval(astor.to_source(node), globals, locals)
            result = ", ".join(repr(x) for x in result)
            return ast.parse(f"[{result}]").body[0].value

        def visit_Call(self, node):
            if ast_utils.is_name(node.func) and node.func.id == "list":
                result = eval(astor.to_source(node), globals, locals)
                result = ", ".join(repr(x) for x in result)
                return ast.parse(f"[{result}]").body[0].value
            return node


            result = eval(astor.to_source(node), globals, locals)
            result = ", ".join(repr(x) for x in result)
            return ast.parse(f"[{result}]").body[0].value
    ListCompSpecializer().visit(tree)


def get_io_type(type_):
    if isinstance(type_, m.BitKind):
        type_ = "bit"
    elif isinstance(type_, m.UIntKind):
        type_ = "uint"
    elif isinstance(type_, m.BitsKind):
        type_ = "bits"
    elif isinstance(type_, m.ArrayKind):
        type_ = "array"
    else:
        raise NotImplementedError(type_)
    return type_


def get_io_width(type_):
    if type_ is magma.Bit:
        return None
    elif isinstance(type_, magma.ArrayKind):
        if isinstance(type_.T, magma.ArrayKind):
            elem_width = get_io_width(type_.T)
            if isinstance(elem_width, tuple):
                return (type_.N, ) + elem_width
            else:
                return (type_.N, elem_width)
        else:
            return type_.N
    else:
        raise NotImplementedError(type_)


def compile(coroutine, file_name=None, mux_strategy="one-hot", output='verilog', strategy="by_statement"):
    if not isinstance(coroutine, Coroutine):
        raise ValueError("silica.compile expects a silica.Coroutine")

    stack = inspect.stack()
    func_locals = stack[1].frame.f_locals
    func_globals = stack[1].frame.f_globals

    has_ce = coroutine.has_ce
    tree = ast_utils.get_ast(coroutine._definition).body[0]  # Get the first element of the ast.Module
    module_name = coroutine._name
    func_locals.update(coroutine._defn_locals)
    func_locals.update(func_globals)
    specialize_arguments(tree, coroutine)
    specialize_constants(tree, coroutine._defn_locals)
    specialize_evals(tree, func_globals, func_locals)
    inline_yield_from_functions(tree, func_globals, func_locals)
    constant_fold(tree)
    specialize_list_comps(tree, func_globals, func_locals)
    tree, list_lens = propagate_types(tree)
    tree, loopvars = desugar_for_loops(tree, list_lens)

    width_table = {}
    type_table = {}
    for input_, type_ in coroutine._inputs.items():
        width_table[input_] = get_io_width(type_)
        type_table[input_] = get_io_type(type_)

    for output_, type_ in coroutine._outputs.items():
        width_table[output_] = get_io_width(type_)
        type_table[output_] = get_io_type(type_)

    for name,width in loopvars:
        width_table[name] = width

    constant_fold(tree)

    for name,_ in loopvars:
        type_table[name] = 'uint'

    # logging.debug("width_table = {width_table}")
    # logging.debug("\n" + astor.to_source(tree))
    CollectInitialWidthsAndTypes(width_table, type_table, func_locals, func_globals).visit(tree)
    PromoteWidths(width_table, type_table).visit(tree)
    tree, loopvars = get_final_widths(tree, width_table, func_locals, func_globals)

    for name,width in loopvars.items():
        width_table[name] = width

    # Desugar(width_table).visit(tree)
    type_table = {}
    TypeChecker(width_table, type_table).check(tree)
    # DesugarArrays().run(tree)
    cfg = ControlFlowGraph(tree, width_table, func_locals, func_globals, coroutine)
    # cfg.render()
    # render_paths_between_yields(cfg.paths)

    if output == 'magma':
        # NOTE: This is currently not maintained
        return compile_magma(coroutine, file_name, mux_strategy, output)

    registers = set()
    for path in cfg.paths:
        registers |= (path[0].live_ins & path[0].live_outs)

    # assert all(outputs[1] == output for output in outputs[1:]), "Yield statements must all have the same outputs except for the first"
    # outputs = outputs[1]
    outputs = tuple(coroutine._outputs.keys())
    states = cfg.states
    num_yields = cfg.curr_yield_id
    num_states = len(states)
    initial_values = {}
    initial_basic_block = False
    sub_coroutines = {}
    # cfg.render()
    for node in cfg.paths[0][:-1]:
        if isinstance(node, HeadBlock):
            for statement in node:
                if ast_utils.is_call(statement.value) and ast_utils.is_name(statement.value.func) and statement.value.func.id == "coroutine_create":
                    sub_coroutine = eval(astor.to_source(statement.value.args[0]), func_globals, func_locals)
                    # statement.value.func = ast.Name(sub_coroutine._name, ast.Load())
                    # statement.value.args = []
                    sub_coroutines[statement.targets[0].id] = compile(sub_coroutine())
                else:
                    if ast_utils.is_name(statement.value) and statement.value.id in initial_values:
                        initial_values[statement.targets[0].id] = initial_values[statement.value.id]
                    else:
                        initial_values[statement.targets[0].id] = get_constant(statement.value)
        initial_basic_block |= isinstance(node, BasicBlock)
    if not initial_basic_block:
        num_states -= 1
        num_yields -= 1
        states = states[1:]
        # for state in states:
        #     state.start_yield_id -= 1
        #     state.end_yield_id -= 1
    num_states = len(states)
    if has_ce:
        raise NotImplementedError("add ce to module decl")

    # declare module and ports
    ctx = verilog.Context(module_name, sub_coroutines)

    def get_len(t):
        try:
            return len(t)
        except Exception:
            return 1

    inputs = { i : width_table.get(i, 1) or 1 for i in coroutine._inputs }
    inputs["CLK"] = 1
    outputs = { o : width_table.get(o, 1) or 1 for o in outputs }
    ctx.declare_ports(inputs, outputs)

    # declare wires
    # for var in cfg.ssa_var_to_curr_id_map:
    #     width = width_table[var]
    #     for i in range(1, cfg.ssa_var_to_curr_id_map[var] + 1):
    #         if f"{var}_{i}" not in registers:
    #             if isinstance(width, MemoryType):
    #                 ctx.declare_wire(f"{var}_{i}", width.width, width.height)
    #             else:
    #                 ctx.declare_wire(f"{var}_{i}", width)
    # cfg.render()
    for var, width in width_table.items():
        if isinstance(width, Coroutine):
            continue
        if var in inputs or var in outputs:
            continue
        if var not in registers:
            if isinstance(width, MemoryType):
                ctx.declare_wire(var, width.width, width.height)
            elif isinstance(width, tuple):
                height = functools.reduce(operator.mul, width[1:])
                width = width[0]
                ctx.declare_wire(var, width, height)
            else:
                ctx.declare_wire(var, width)

    for (name, index), (value, orig_value) in cfg.replacer.array_stores.items():
        width = width_table[name]
        if isinstance(width, MemoryType):
            width = width.width
        else:
            width = None
        if len(index) > 1: raise NotImplementedError()
        index_hash = "_".join(ast.dump(i) for i in index)
        count = cfg.replacer.index_map[index_hash]
        for i in range(count + 1):
            var = name + f"_si_tmp_val_{value}_i{i}"
            if var not in width_table:
                width_table[var] = width
                ctx.declare_wire(var, width)

    # declare regs
    for register in registers:
        width = width_table[register]
        if isinstance(width, Coroutine):
            continue
        if isinstance(width, MemoryType):
            ctx.declare_reg(register, width.width, width.height)
        else:
            ctx.declare_reg(register, width)

    init_body = [ctx.assign(ctx.get_by_name(key), value) for key,value in initial_values.items() if value is not None]

    for sub_coroutine in sub_coroutines:
        for key, type_ in sub_coroutines[sub_coroutine].interface.ports.items():
            if key == "CLK":
                continue
            if isinstance(type_, m.BitType):
                width = None
            else:
                width = len(type_)
            ctx.declare_wire(f"_si_{sub_coroutine}_{key}", width)

    if cfg.curr_yield_id > 1:
        yield_state_width = (cfg.curr_yield_id - 1).bit_length()
        ctx.declare_reg("yield_state", yield_state_width)
        ctx.declare_wire(f"yield_state_next", yield_state_width)
        init_body.append(ctx.assign(ctx.get_by_name("yield_state"), 0))

    # if initial_basic_block:
    #     for statement in states[0].statements:
    #         verilog.process_statement(statement)
            # init_body.append(ctx.translate(statement)) # TODO: redefinition bug?
            # temp_var_promoter.visit(statement)

    ctx.initial(init_body)

    raddrs = {}
    waddrs = {}
    wdatas = {}
    wens = {}
    # if initial_basic_block:
    #     states = states[1:]
    verilog.compile_states(ctx, states, cfg.curr_yield_id == 3, width_table,
                           registers, sub_coroutines, strategy)
    # cfg.render()
    verilog_str = ""
    for sub_coroutine in sub_coroutines.values():
        verilog_str += sub_coroutine.verilogFile
    verilog_str += ctx.to_verilog()

    if file_name is not None:
        with open(file_name, "w") as f:
            f.write(verilog_str)
    return m.DefineFromVerilog(verilog_str, type_map={"CLK": m.In(m.Clock)}, target_modules=[coroutine._name])[0]
