// receiver.c
//
// This file implements the receiver functionality for a simple digital signal
// transmission system using the pigpio library on a Raspberry Pi.
// It now writes the first 15 bits (the “flag bits”) to flag.txt, then continues
// to collect the rest of the data and writes it to received.txt.

#include <stdio.h>
#include <stdlib.h>
#include <time.h>       // for clock_nanosleep() and time functions
#include <pigpio.h>     // pigpio C library
#include <string.h>
#include <stdint.h>
#include <pthread.h>    // for mutex in callbacks

// ---------------------
// Receiver Definitions
// ---------------------
#define RECV_PIN1 23
#define RECV_PIN0 24
#define MAX_BUFFER_SIZE 150000

// Global buffer and synchronization
char received_buffer[MAX_BUFFER_SIZE];
volatile int buffer_index = 0;
pthread_mutex_t buffer_mutex = PTHREAD_MUTEX_INITIALIZER;

// Timestamp of last received bit
volatile time_t last_signal_time = 0;

// ---------------------
// Utility: precise_sleep
// ---------------------
void precise_sleep(long nanoseconds) {
    struct timespec ts;
    ts.tv_sec  = nanoseconds / 1000000000L;
    ts.tv_nsec = nanoseconds % 1000000000L;
    clock_nanosleep(CLOCK_MONOTONIC, 0, &ts, NULL);
}

// ---------------------
// Callback for '1' bits
// ---------------------
void callback_bit1(int gpio, int level, uint32_t tick) {
    static int last_level = 0;
    if (level == 1 && last_level == 0) { // rising edge
        pthread_mutex_lock(&buffer_mutex);
        if (buffer_index < MAX_BUFFER_SIZE - 1)
            received_buffer[buffer_index++] = '1';
        last_signal_time = time(NULL);
        pthread_mutex_unlock(&buffer_mutex);
    }
    last_level = level;
}

// ---------------------
// Callback for '0' bits
// ---------------------
void callback_bit0(int gpio, int level, uint32_t tick) {
    static int last_level = 0;
    if (level == 1 && last_level == 0) { // rising edge
        pthread_mutex_lock(&buffer_mutex);
        if (buffer_index < MAX_BUFFER_SIZE - 1)
            received_buffer[buffer_index++] = '0';
        last_signal_time = time(NULL);
        pthread_mutex_unlock(&buffer_mutex);
    }
    last_level = level;
}

// ---------------------
// Main receiver logic
// ---------------------
void receiver_main(void) {
    // Configure pins as inputs
    gpioSetMode(RECV_PIN1, PI_INPUT);
    gpioSetMode(RECV_PIN0, PI_INPUT);

    // Register callbacks for level changes
    gpioSetAlertFunc(RECV_PIN1, callback_bit1);
    gpioSetAlertFunc(RECV_PIN0, callback_bit0);

    printf("Receiver: Waiting for flag bits...\n");

    // Wait until at least 15 bits (the flag) have been received
    while (1) {
        pthread_mutex_lock(&buffer_mutex);
        int idx = buffer_index;
        pthread_mutex_unlock(&buffer_mutex);
        if (idx >= 15) break;
        precise_sleep(10000000L); // 10 ms
    }

    // Extract the first 15 bits into a local string
    char flag_bits[16];  // 15 bits + null terminator
    pthread_mutex_lock(&buffer_mutex);
    memcpy(flag_bits, received_buffer, 15);
    flag_bits[15] = '\0';

    // Remove them from the buffer
    memmove(received_buffer,
            received_buffer + 15,
            buffer_index - 15);
    buffer_index -= 15;
    pthread_mutex_unlock(&buffer_mutex);

    // Write the flag bits to flag.txt
    FILE *flagfile = fopen("flag.txt", "w");
    if (!flagfile) {
        perror("Receiver: Error opening flag.txt");
    } else {
        fprintf(flagfile, "%s", flag_bits);
        fclose(flagfile);
    }

    // Ensure we have a starting timestamp for subsequent bits
    pthread_mutex_lock(&buffer_mutex);
    if (last_signal_time == 0)
        last_signal_time = time(NULL);
    pthread_mutex_unlock(&buffer_mutex);

    printf("Receiver: Flag bits saved, now receiving data...\n");

    // Continue collecting until 5 seconds of inactivity
    while (1) {
        time_t now = time(NULL);
        pthread_mutex_lock(&buffer_mutex);
        time_t last = last_signal_time;
        pthread_mutex_unlock(&buffer_mutex);
        if (difftime(now, last) >= 5.0)
            break;
        precise_sleep(10000000L); // 10 ms
    }

    // Stop callbacks
    gpioSetAlertFunc(RECV_PIN1, NULL);
    gpioSetAlertFunc(RECV_PIN0, NULL);

    // Null-terminate remaining data and write to received.txt
    pthread_mutex_lock(&buffer_mutex);
    received_buffer[buffer_index] = '\0';
    pthread_mutex_unlock(&buffer_mutex);

    FILE *outfile = fopen("received.txt", "w");
    if (!outfile) {
        perror("Receiver: Error opening received.txt");
    } else {
        fprintf(outfile, "%s", received_buffer);
        fclose(outfile);
    }

    printf("Receiver: Reception complete. %d bits written to received.txt.\n", buffer_index);
}

// ---------------------
// Program entry point
// ---------------------
int main(void) {
    // Initialize pigpio
    if (gpioInitialise() < 0) {
        fprintf(stderr, "Failed to initialize pigpio.\n");
        return 1;
    }

    receiver_main();

    gpioTerminate();
    return 0;
}
