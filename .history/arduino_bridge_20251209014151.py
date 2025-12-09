import serial
import serial.tools.list_ports
import time
import threading

class ArduinoBridge:
    """
    Cầu nối giữa Arduino và Flask Server
    Thay thế arduino_simulation_loop() trong app.py
    """
    
    def __init__(self, callback_pir=None, callback_rfid=None, callback_pet=None):
        self.serial_port = None
        self.is_connected = False
        self.callback_pir = callback_pir
        self.callback_rfid = callback_rfid
        self.callback_pet = callback_pet
        
    def find_arduino(self):
        """Tự động tìm Arduino port"""
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            # Arduino thường có description chứa "Arduino" hoặc "CH340"
            if "Arduino" in port.description or "CH340" in port.description or "USB" in port.description:
                return port.device
        
        # Nếu không tìm thấy, thử các port thông thường
        for port_name in ["COM3", "COM4", "COM5", "/dev/ttyUSB0", "/dev/ttyACM0"]:
            try:
                test_port = serial.Serial(port_name, 115200, timeout=1)
                test_port.close()
                return port_name
            except:
                continue
        
        return None
    
    def connect(self, port=None):
        """Kết nối với Arduino"""
        if port is None:
            port = self.find_arduino()
        
        if port is None:
            print("❌ Không tìm thấy Arduino!")
            return False
        
        try:
            self.serial_port = serial.Serial(port, 115200, timeout=1)
            time.sleep(2)  # Đợi Arduino reset
            
            # Đọc thông báo khởi động
            while self.serial_port.in_waiting:
                line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                print(f"Arduino: {line}")
            
            self.is_connected = True
            print(f"✅ Đã kết nối Arduino tại {port}")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi kết nối: {e}")
            return False
    
    def send_command(self, cmd):
        """Gửi lệnh đến Arduino"""
        if not self.is_connected or self.serial_port is None:
            return False
        
        try:
            self.serial_port.write(f"{cmd}\n".encode())
            return True
        except Exception as e:
            print(f"❌ Lỗi gửi lệnh: {e}")
            return False
    
    def read_loop(self):
        """Vòng lặp đọc dữ liệu từ Arduino"""
        print("🔄 Bắt đầu đọc dữ liệu từ Arduino...")
        
        while self.is_connected:
            try:
                if self.serial_port and self.serial_port.in_waiting:
                    line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    
                    if not line:
                        continue
                    
                    print(f"📡 Arduino: {line}")
                    
                    # Xử lý PIR
                    if line.startswith("PIR:"):
                        pir_value = int(line.split(":")[1])
                        if self.callback_pir:
                            self.callback_pir(pir_value)
                    
                    # Xử lý RFID
                    elif line.startswith("RFID:"):
                        rfid_tag = line.split(":", 1)[1]
                        if self.callback_rfid:
                            self.callback_rfid(rfid_tag)
                    
                    # Xử lý response
                    elif line == "PONG":
                        print("✅ Arduino phản hồi PING")
                
                time.sleep(0.01)
                
            except Exception as e:
                print(f"❌ Lỗi đọc: {e}")
                time.sleep(0.1)
    
    def start(self):
        """Khởi động thread đọc dữ liệu"""
        if not self.is_connected:
            print("❌ Chưa kết nối Arduino!")
            return False
        
        thread = threading.Thread(target=self.read_loop, daemon=True)
        thread.start()
        return True
    
    def close(self):
        """Đóng kết nối"""
        self.is_connected = False
        if self.serial_port:
            self.serial_port.close()
        print("🔌 Đã ngắt kết nối Arduino")


# ===============================
# TEST STANDALONE
# ===============================
if __name__ == "__main__":
    def on_pir(value):
        print(f"🚨 PIR: {value}")
    
    def on_rfid(tag):
        print(f"🏷️  RFID: {tag}")
    
    bridge = ArduinoBridge(
        callback_pir=on_pir,
        callback_rfid=on_rfid
    )
    
    if bridge.connect():
        bridge.start()
        
        print("\n🎮 Test commands:")
        print("  1 - Gửi PET_DETECTED")
        print("  2 - Gửi NO_PET")
        print("  3 - Gửi PING")
        print("  q - Thoát\n")
        
        try:
            while True:
                cmd = input("Command: ").strip()
                
                if cmd == "q":
                    break
                elif cmd == "1":
                    bridge.send_command("PET_DETECTED")
                elif cmd == "2":
                    bridge.send_command("NO_PET")
                elif cmd == "3":
                    bridge.send_command("PING")
                
        except KeyboardInterrupt:
            pass
        
        bridge.close()
    
    print("👋 Bye!")