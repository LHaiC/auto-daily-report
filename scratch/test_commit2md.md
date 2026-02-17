# Raw Notes - 2026-02-17

- Spent morning debugging UART driver on STM32F4. Baud rate was off by 3% due to wrong APB1 clock divider.
- Fixed the prescaler calculation in `uart_init()`. Verified with logic analyzer: 115200 baud now within 0.5% tolerance.
- Reviewed PR #42 for SPI DMA refactor. Left comments about missing cache invalidation on Cortex-M7.
- Started reading about Steiner tree algorithms for PCB routing optimization.
- Blocker: CI pipeline broken since yesterday, Docker image pull rate-limited on GitHub Actions.
- TODO tomorrow: write unit tests for the new UART config parser.
