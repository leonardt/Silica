import ast
import astor


class ConstantFold(ast.NodeTransformer):
    def visit_BinOp(self, node):
        node.left = self.visit(node.left)
        node.right = self.visit(node.right)
        if (isinstance(node.left, ast.Num) or \
            isinstance(node.left, ast.UnaryOp) and \
            isinstance(node.left.op, ast.USub) and isinstance(node.left.operand, ast.Num)) and \
           (isinstance(node.right, ast.Num) or \
            isinstance(node.right, ast.UnaryOp) and \
            isinstance(node.right.op, ast.USub) and isinstance(node.right.operand, ast.Num)):
                result = eval(astor.to_source(node))
                if result is True or result is False:
                    return ast.NameConstant(result)
                if result >= 0:
                    return ast.Num(result)
                else:
                    return ast.UnaryOp(ast.USub(), ast.Num(result))
        elif isinstance(node.op, ast.Mult) and \
             ((isinstance(node.left, ast.Num) and node.left.n == 0) or
              (isinstance(node.right, ast.Num) and node.right.n == 0)):
            return ast.Num(0)
        elif isinstance(node.op, ast.Add):
            if isinstance(node.left, ast.Num) and node.left.n == 0:
                return node.right
            elif isinstance(node.right, ast.Num) and node.right.n == 0:
                return node.left
        return node

    def visit_Compare(self, node):
        node.left = self.visit(node.left)
        node.comparators = [self.visit(x) for x in node.comparators]
        if isinstance(node.left, ast.Num) and all(isinstance(comparator, ast.Num) for comparator in node.comparators):
            result = eval(astor.to_source(node))
            if result is True or result is False:
                return ast.NameConstant(result)
            return ast.Num(result)
        return node

def constant_fold(tree):
    return ConstantFold().visit(tree)
