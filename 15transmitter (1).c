// transmitter.c
#include <stdio.h>
#include <stdlib.h>
#include <time.h>      // for clock_nanosleep() and time functions
#include <pigpio.h>    // pigpio C library
#include <string.h>
#include <stdint.h>

// ---------------------
// Transmitter Definitions
// ---------------------
#define GPIO_BIT1 18  // Transmit a '1'
#define GPIO_BIT0 19  // Transmit a '0'

#define BITRATE 3000                       // 3 kbps
#define BIT_DURATION_NS 219333L            // One bit period in ns
#define HIGH_DURATION_NS 76333L            // HIGH time (~40% duty cycle)
#define LOW_DURATION_NS (BIT_DURATION_NS - HIGH_DURATION_NS)

typedef struct {
    char *filename;
    int flag; // 0 for text, 1 for voice
} TXArgs;

void precise_sleep(long nanoseconds) {
    struct timespec ts;
    ts.tv_sec  = nanoseconds / 1000000000L;
    ts.tv_nsec = nanoseconds % 1000000000L;
    clock_nanosleep(CLOCK_MONOTONIC, 0, &ts, NULL);
}

void transmitter_main(TXArgs *txArgs) {
    char *filename = txArgs->filename;
    int flag       = txArgs->flag;

    // init pins
    gpioSetMode(GPIO_BIT1, PI_OUTPUT);
    gpioSetMode(GPIO_BIT0, PI_OUTPUT);
    gpioWrite(GPIO_BIT1, 0);
    gpioWrite(GPIO_BIT0, 0);

    // --- Send the flag bit 15 times ---
    for (int i = 0; i < 15; i++) {
        if (flag == 0) {
            // send '0'
            gpioWrite(GPIO_BIT1, 0);
            gpioWrite(GPIO_BIT0, 1);
        } else {
            // send '1'
            gpioWrite(GPIO_BIT0, 0);
            gpioWrite(GPIO_BIT1, 1);
        }
        precise_sleep(HIGH_DURATION_NS);
        // turn both off
        gpioWrite(GPIO_BIT0, 0);
        gpioWrite(GPIO_BIT1, 0);
        precise_sleep(LOW_DURATION_NS);
    }

    // pause before data
    precise_sleep(2000000000L);

    // rest unchanged: read file, loop through bits, send as before...
    FILE *file = fopen(filename, "r");
    if (!file) { perror("Transmitter: Error opening bitstream file"); return; }
    fseek(file, 0, SEEK_END);
    long length = ftell(file);
    rewind(file);
    char *buffer = malloc(length + 1);
    if (!buffer) { perror("Transmitter: Failed to allocate memory"); fclose(file); return; }
    fread(buffer, 1, length, file);
    buffer[length] = '\0';
    fclose(file);

    printf("Transmitter: First 10 bits: %.10s\n", buffer);
    printf("Transmitter: Transmitting PWM at %d bps from '%s'...\n", BITRATE, filename);

    long transmitted_bits = 0;
    for (long i = 0; i < length; i++) {
        char b = buffer[i];
        if (b == '1') {
            gpioWrite(GPIO_BIT0, 0);
            gpioWrite(GPIO_BIT1, 1);
            precise_sleep(HIGH_DURATION_NS);
            gpioWrite(GPIO_BIT1, 0);
            precise_sleep(LOW_DURATION_NS);
            transmitted_bits++;
        } else if (b == '0') {
            gpioWrite(GPIO_BIT1, 0);
            gpioWrite(GPIO_BIT0, 1);
            precise_sleep(HIGH_DURATION_NS);
            gpioWrite(GPIO_BIT0, 0);
            precise_sleep(LOW_DURATION_NS);
            transmitted_bits++;
        }
    }

    printf("Transmitter: Transmission complete. %ld bits sent.\n", transmitted_bits);
    free(buffer);
}

int main(int argc, char *argv[]) {
    if (argc != 3) {
        printf("Usage: %s <bitstream_file> <flag (0 for text, 1 for voice)>\n", argv[0]);
        return 1;
    }
    int flag = atoi(argv[2]);
    if (flag != 0 && flag != 1) {
        fprintf(stderr, "Error: flag must be 0 (text) or 1 (voice).\n");
        return 1;
    }
    if (gpioInitialise() < 0) {
        fprintf(stderr, "Failed to initialize pigpio.\n");
        return 1;
    }
    TXArgs txArgs = { .filename = argv[1], .flag = flag };
    transmitter_main(&txArgs);
    gpioTerminate();
    return 0;
}
