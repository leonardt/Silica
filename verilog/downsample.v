module downsample_verilog(
    input data_in_valid,
    input [15:0] data_in_data,
    output data_in_ready,
    output data_out_valid,
    output [15:0] data_out_data,
    input data_out_ready,
    input CLK,
    input RESET
);
reg [4:0] x;
reg [4:0] y;
reg [4:0] x_next;
reg [4:0] y_next;

wire keep;

assign keep = (x % 2 == 0) & (y % 2 == 0);
assign data_out_valid = keep & data_in_valid;
assign data_in_ready = data_out_ready | ~keep;
assign data_out_data = data_in_data;

always @(*) begin
    if (data_in_ready & data_in_valid) begin
        x_next = x + 1;
        if (x == 31) begin
            y_next = y + 1;
        end else begin
            y_next = y;
        end
    end else begin
        x_next = x;
        y_next = y;
    end
end


always @(posedge CLK or posedge RESET) begin
    if (RESET) begin
        x <= 0;
        y <= 0;
    end else begin
        x <= x_next;
        y <= y_next;
    end
end
endmodule
