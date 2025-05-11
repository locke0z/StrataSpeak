import subprocess
import time
import os
import sys

def on_send_a_button_press(hq_flag):
    print("In sending audio mode! Starting the pipeline...")
    
    # 1. Record audio and ADC
    
    #Check file exist
    wav_path = 'input.wav'
    if not os.path.exists(wav_path):
        raise RuntimeError("Input wav file doesn't exist!")
        
    #Check if file is not empty
    elif os.path.getsize(wav_path) == 0:
        raise ValueError("Error: input.wav is empty.")
 
    # 2. Compress audio
    
    #subprocess.run(["source", "mlow-env/bin/activate"]) #virtual env
    else
        print("Starting compression...")
    #result = subprocess.call("time encodec -b 6 -f input.wav compressed.ecdc", shell=True, executable='/bin/bash')
    if hq_flag:
        result = subprocess.call("time opusenc --bitrate 12 --speech --cvbr input.wav compressed.opus", shell=True, executable='/bin/bash')
    else:
        result = subprocess.call("time opusenc --bitrate 6 --speech --cvbr input.wav compressed.opus", shell=True, executable='/bin/bash')
    #print(result)
    
    if result!= 0:
        raise RuntimeError("Compression process didn't finish properly!")

    #Check process finished
    elif not os.path.exists("compressed.opus"):
        raise RuntimeError("Compression failed!")
        
    #Check if file is not empty
    elif os.path.getsize("compressed.opus") == 0:
        raise ValueError("Error: compressed.opus is empty. Compression may have failed.")
    else
        print("Compression done!")
    
    # 3. Convert to bitstream
    
    print("Starting extracting bitstream...")
    result = subprocess.call("xxd -b compressed.opus | cut -d' ' -f2-7 | tr -d ' \n' > bitstream.txt", shell=True, executable='/bin/bash')
    if result!= 0:
        raise RuntimeError("Extracting didn't finish properly!")
        #Check process finished
    elif not os.path.exists("bitstream.txt"):
        raise RuntimeError("extracting failed!")
    #Check if file is not empty
    elif os.path.getsize("bitstream.txt") == 0:
        raise ValueError("Error: bitstream.txt is empty. Extracting may have failed.")
    else
        print("Extracting done!")
    
    # 4. Transmit bitstream
    
    try:
        result = subprocess.call("'./transmitter' bitstream.txt 1", shell=True, executable='/bin/bash')
        print("Transmission compelete!")
    except subprocess.CalledProcessError as e:
        print(f"Error: transmission failed with return code {e.returncode}")
    
    #subprocess.run(["deactivate"]) #exit virtual env
    
def on_send_t_button_press():
    print("In sending text mode! Starting the pipeline...")
    
    # 1. Input text
    #Check file exist
    txt_path = 'txtmsg.txt'
    if not os.path.exists(txt_path):
        raise RuntimeError("Input text file doesn't exist!")
        
    #Check if file is not empty
    elif os.path.getsize(txt_path) == 0:
        raise ValueError("Error: txtmsg.txt is empty.")
        
    # 2. Convert to bitstream
    stream_path = "bitstream.txt"
    
    print("Starting extracting bitstream...")
    result = subprocess.call("xxd -b txtmsg.txt | cut -d' ' -f2-7 | tr -d ' \n' > bitstream.txt", shell=True, executable='/bin/bash')
    if result!= 0:
        raise RuntimeError("Extracting didn't finish properly!")
        #Check process finished
    elif not os.path.exists(stream_path):
        raise RuntimeError("extracting failed!")
    #Check if file is not empty
    elif os.path.getsize(stream_path) == 0:
        raise ValueError("Error: bitstream.txt is empty. Extracting may have failed.")
    else
        print("Extracting done!")
    
    # 3. Transmit bitstream
    try:
        result = subprocess.call("'./transmitter' bitstream.txt 0", shell=True, executable='/bin/bash')
        print("Transmission compelete!")
    except subprocess.CalledProcessError as e:
        print(f"Error: transmission failed with return code {e.returncode}")

def on_receive_a_button_press():
    print("Starting audio reconstruction...")
    
    # Define the Received folder path under the home directory
    '''home_dir = os.path.expanduser("~")
    received_dir = os.path.join(home_dir, "Received")'''
    received_dir = "Received"
    
    # Ensure the directory exists (just in case)
    os.makedirs(received_dir, exist_ok=True)
    
    #save every file received
    i = 1
    while os.path.exists(os.path.join(received_dir, f"reconstructed{i}.opus")):
        i += 1
    opus_filename = os.path.join(received_dir, f"reconstructed{i}.opus")
    
    print(opus_filename)
    
    '''# 3. Receive bitstream
    try:
        result = subprocess.call("./receiver", shell=True, executable='/bin/bash')
    except subprocess.CalledProcessError as e:
        print(f"Error: Receiving failed with return code {e.returncode}")'''
        
    # 1. Reconstruct opus file
    with open("received.txt", "r") as f:
        bitstream = f.read().replace(" ", "").replace("\n", "")  # Ignore spaces & newlines

    '''# Ensure bitstream length is a multiple of 8
    if len(bitstream) % 8 != 0:
        raise ValueError("Bitstream length is not a multiple of 8!")'''

    # Convert bitstream to bytes
    byte_data = bytearray(int(bitstream[i:i+8], 2) for i in range(0, len(bitstream), 8))

    # Write to output file
    with open(opus_filename, "wb") as f:
        f.write(byte_data)

    print(f"Reconstructed {opus_filename} successfully!")
    
    # 2. Decompress        
    if not os.path.isfile(opus_filename):
        print(f"Error: File '{opus_filename}' does not exist.")
        return

    # Try to run ffplay and check return code
    try:
        result = subprocess.call(f"ffplay -autoexit -nodisp {opus_filename}", shell=True, executable='/bin/bash')
        print(f"ffplay -autoexit -nodisp {opus_filename}")
        if result != 0:
            print(f"Error: ffplay exited with return code {result}")
    except FileNotFoundError:
        print("Error: ffplay not found. Please install FFmpeg to play audio.")
    except Exception as e:
        print(f"An unexpected error occurred while playing the file: {e}")
        
    print(f"Decompression done! Saved as {opus_filename}")

def on_receive_t_button_press():
    
    '''# 3. Receive bitstream
    try:
        result = subprocess.call("./receiver", shell=True, executable='/bin/bash')
    except subprocess.CalledProcessError as e:
        print(f"Error: Receiving failed with return code {e.returncode}")'''
        
    print("Starting text reconstruction...")
    
    # Read the bitstream
    
    with open("received.txt", "r") as f:
        bits = f.read().strip()

    # Break into bytes
    bytes_list = [bits[i:i+8] for i in range(0, len(bits), 8)]
    
    # Define the Received folder path under the home directory
    received_dir = "/home/group3/Received"
    # Ensure the directory exists 
    os.makedirs(received_dir, exist_ok=True)
    
    #save every file received
    i = 1
    while os.path.exists(os.path.join(received_dir, f"recovered{i}.txt")):
        i += 1
    output_filename = os.path.join(received_dir, f"recovered{i}.txt")
    # Convert to characters and write to a file
    with open(output_filename, "wb") as out:
        for byte in bytes_list:
            if len(byte) == 8:
                out.write(int(byte, 2).to_bytes(1, byteorder='big'))
    print(f"Reconstruction done! Saved as {output_filename}" )
    
def decide_receive_based_on_flag():
    # Receive bitstream
    try:
        result = subprocess.call("./receiver", shell=True, executable='/bin/bash')
    except subprocess.CalledProcessError as e:
        print(f"Error: Receiving failed with return code {e.returncode}")
        
    flag_file = "flag.txt"

    # Check if flag.txt exists
    if not os.path.isfile(flag_file):
        print("Error: flag.txt not found!")
        return

    # Read the file and count '1's
    with open(flag_file, 'r') as f:
        content = f.read()

    num_ones = content.count('1')
    print(f"Number of '1's in flag.txt: {num_ones}")
    
    # Decide based on number of '1's
    if 6 < num_ones < 10:
        print("Signal is lossy — attempting to recover both audio and text.")
        print("Receiving audio...")
        on_receive_a_button_press()
        print("Receiving text...")
        on_receive_t_button_press()
    elif num_ones >= 10:
        print("10 or more '1's detected. Receiving audio...")
        on_receive_a_button_press()
    else:
        print("7 or fewer '1's detected. Receiving text...")
        on_receive_t_button_press()
     

def replay_saved_files():
    received_dir = os.path.expanduser("/home/group3/Received")
    env = os.environ.copy()
    
    print(received_dir)
    print("Available .opus and .txt files:")

    # Get list of .txt and .opus files in the Received folder
    files = [f for f in os.listdir(received_dir) if f.endswith('.opus') or f.endswith('.txt')]
    if not files:
        print("No saved files found in ~/Received.")
        return

    for idx, file in enumerate(files, start=1):
        print(f"{idx}. {file}")

    try:
        choice = int(input("Enter the number of the file you want to replay/display: ")) - 1
        if 0 <= choice < len(files):
            selected_file = files[choice]
            full_path = os.path.join(received_dir, selected_file)
            print(f"You selected: {selected_file}")

            if selected_file.endswith('.txt'):
                with open(full_path, 'r') as f:
                    print("---- FILE CONTENT ----")
                    print(f.read())
                    print("----------------------")
            elif selected_file.endswith('.opus'):
                print("Playing audio...")
                if not os.path.isfile(full_path):
                    print(f"Error: File '{full_path}' does not exist.")
                    return
                try:
                    result = subprocess.call(f"ffplay -autoexit \"{full_path}\"", shell=True, executable='/bin/bash', env=env)
                    if result != 0:
                        print(f"Error: ffplay exited with return code {result}")
                except FileNotFoundError:
                    print("Error: ffplay not found. Please install FFmpeg to play audio.")
                except Exception as e:
                    print(f"An unexpected error occurred while playing the file: {e}")
            else:
                print("Unsupported file type.")
        elif choice == '100':
            return
        else:
            print("Invalid selection.")
    except ValueError:
        print("Please enter a valid number.")
        
def main():
    # Clear GPIO pins
    try:
        result = subprocess.call("sudo killall pigpiod", shell=True, executable='/bin/bash')

        while True:
            user_input = input("\nInput sa to send audio, sa_hq to send high quality (but slow) audio, ra to receive audio, st to send text, rt to receive text, replay to replay saved files, q to exit! : ").strip().lower()

            if user_input == 'sa':
                hq_flag = 0
                on_send_a_button_press(hq_flag)
                time.sleep(1)  # debounce delay
            elif user_input == 'sa_hq':
                hq_flag = 1
                on_send_a_button_press(hq_flag)
                time.sleep(1)  # debounce delay   
                '''elif user_input == 'ra':
                on_receive_a_button_press()
                time.sleep(1)  # debounce delay'''
            elif user_input == 'st':
                on_send_t_button_press()
                time.sleep(1)  # debounce delay
                '''elif user_input == 'rt':
                on_receive_t_button_press()
                time.sleep(1)  # debounce delay'''
            elif user_input == 'r':
                decide_receive_based_on_flag()
                time.sleep(1)  # debounce delay
            elif user_input == 'replay':
                replay_saved_files()
                time.sleep(1)  # debounce delay 
            elif user_input == 'q':
                print("Exiting...")
                break;
            else:
                print("invalid input, try again")

    except KeyboardInterrupt:
        print("\nInterrupted by user, exiting")

if __name__ == "__main__":
    main()

