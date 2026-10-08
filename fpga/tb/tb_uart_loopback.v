`timescale 1ns/1ps

module tb_uart_loopback;

    // ============================================================
    // Parameters
    // ============================================================
    localparam integer CLK_PERIOD = 20;      // 50 MHz = 20 ns
    localparam integer BIT_TIME   = 8681;    // 115200 baud ≈ 8681 ns/bit

    // ============================================================
    // Testbench signals
    // ============================================================
    reg  clk;
    reg  rst_n;
    reg  uart_rx;

    wire uart_tx;
    wire led;

    // ============================================================
    // Instantiate DUT
    // ============================================================
    ac620_uart_loopback_top dut (
        .clk     (clk),
        .rst_n   (rst_n),
        .uart_rx (uart_rx),
        .uart_tx (uart_tx),
        .led     (led)
    );

    // ============================================================
    // 50 MHz clock
    // ============================================================
    initial begin
        clk = 1'b0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    // ============================================================
    // UART transmit task
    // Simulates PC sending one byte to FPGA
    // 8N1: 1 start + 8 data + 1 stop
    // ============================================================
    task uart_send_byte;
        input [7:0] data;
        integer i;
        begin
            // Start bit
            uart_rx = 1'b0;
            #(BIT_TIME);

            // 8 data bits, LSB first
            for (i = 0; i < 8; i = i + 1) begin
                uart_rx = data[i];
                #(BIT_TIME);
            end

            // Stop bit
            uart_rx = 1'b1;
            #(BIT_TIME);

            // Gap between bytes
            #(BIT_TIME);
        end
    endtask

    // ============================================================
    // Main simulation
    // ============================================================
    initial begin

        // UART idle state
        uart_rx = 1'b1;

        // Reset
        rst_n = 1'b0;

        #200;

        rst_n = 1'b1;

        // Wait after reset
        #20000;

        // Send 55 AA 12 34
        uart_send_byte(8'h55);
        uart_send_byte(8'hAA);
        uart_send_byte(8'h12);
        uart_send_byte(8'h34);

        // Wait for FPGA to finish loopback transmission
        #500000;

        $stop;
    end

endmodule