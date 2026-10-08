`timescale 1ns/1ps

module tb_mean_filter_3x3;

    reg clk;
    reg rst_n;

    reg  [7:0] pixel_in;
    reg        pixel_valid;

    wire [7:0] pixel_out;
    wire       pixel_out_valid;

    integer col;

    // 实例化均值滤波器
    mean_filter_3x3 dut (
        .clk            (clk),
        .rst_n          (rst_n),
        .pixel_in       (pixel_in),
        .pixel_valid    (pixel_valid),
        .pixel_out      (pixel_out),
        .pixel_out_valid(pixel_out_valid)
    );

    // 50 MHz 时钟
    initial begin
        clk = 0;
        forever #10 clk = ~clk;
    end

    // 发送一个像素
    task send_pixel;
        input [7:0] data;
        begin
            @(negedge clk);
            pixel_in    = data;
            pixel_valid = 1'b1;

            @(negedge clk);
            pixel_valid = 1'b0;
        end
    endtask

    initial begin

        rst_n       = 0;
        pixel_in    = 0;
        pixel_valid = 0;

        #100;
        rst_n = 1;

        // ==========================
        // 第0行
        // 10 20 30 0 0 ...
        // ==========================
        send_pixel(10);
        send_pixel(20);
        send_pixel(30);

        for (col = 3; col < 256; col = col + 1)
            send_pixel(0);

        // ==========================
        // 第1行
        // 40 50 60 0 0 ...
        // ==========================
        send_pixel(40);
        send_pixel(50);
        send_pixel(60);

        for (col = 3; col < 256; col = col + 1)
            send_pixel(0);

        // ==========================
        // 第2行
        // 70 80 90
        // ==========================
        send_pixel(70);
        send_pixel(80);
        send_pixel(90);

        #200;

        $stop;

    end

endmodule