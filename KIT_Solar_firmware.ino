// Battery Voltage Monitoring Pins
#define BATTERY_1S_VOLTAGE_PIN A0
#define BATTERY_2S_VOLTAGE_PIN A1
#define BATTERY_3S_VOLTAGE_PIN A2
#define BATTERY_TOTAL_VOLTAGE_PIN A3

// Digital Input Pins
#define PUSHBUTTON_GREEN_INPUT_PIN 10        // 푸시버튼 녹
#define PUSHBUTTON_RED_INPUT_PIN 11          // 푸시버튼 적

// Digital Output Pins (새로운 핀들로 교체)
#define PILOT_LAMP_GREEN_RED_OUTPUT_PIN 5    // 파일럿램프 녹/적(NO/NC)
#define FAN_COMMERCIAL_SMPS_OUTPUT_PIN 6     // 선풍기 부하(상용/SMPS)
#define FAN_BATTERY_MODULE_OUTPUT_PIN 7      // 선풍기 부하(이차전지모듈)
#define HALOGEN_LAMP_OUTPUT_PIN 8            // 할로겐램프



// Output Control States
typedef enum _PilotLampState
{
  PILOT_LAMP_OFF,
  PILOT_LAMP_GREEN,
  PILOT_LAMP_RED
} PilotLampState;

typedef enum _FanState
{
  FAN_OFF,
  FAN_ON
} FanState;

typedef enum _HalogenLampState
{
  HALOGEN_LAMP_OFF,
  HALOGEN_LAMP_ON
} HalogenLampState;

// Push Button Input States
typedef enum _PushButtonState
{
  BUTTON_RELEASED,
  BUTTON_PRESSED
} PushButtonState;

// Global Control Variables
PilotLampState PilotLampControl = PILOT_LAMP_OFF;
FanState FanCommercialControl = FAN_OFF;
FanState FanBatteryControl = FAN_OFF;
HalogenLampState HalogenLampControl = HALOGEN_LAMP_OFF;

// Global Variables for Input States
PushButtonState GreenButtonState = BUTTON_RELEASED;
PushButtonState RedButtonState = BUTTON_RELEASED;
int greenButtonInput;               // 녹색 푸시버튼 입력
int redButtonInput;                 // 적색 푸시버튼 입력

// Battery Voltage Variables
int battery1sVoltage;
int battery2sVoltage;
int battery3sVoltage;
int batteryTotalVoltage;

// Voltage Sensor Configuration
const float VOLTAGE_SENSOR_RATIO = 5.0;  // 전압 분배비 (25V -> 5V)
const float ARDUINO_REF_VOLTAGE = 5.0;   // 아두이노 기준 전압
const int ADC_RESOLUTION = 1024;         // 10비트 ADC 해상도

// Calculated Voltage Variables
float voltage1s_real;      // 1S 실제 전압 (V)
float voltage2s_real;      // 2S 실제 전압 (V)  
float voltage3s_real;      // 3S 실제 전압 (V)
float voltageTotal_real;   // 총 실제 전압 (V)

// System Control Constants
const float BATTERY_THRESHOLD_VOLTAGE = 10.0;    // 배터리 임계 전압 (10V)
const unsigned long AUTO_CONTROL_INTERVAL = 500; // 자동 제어 주기 (0.5초)

// System Status Variables
bool batteryVoltageOK = false;        // 배터리 전압 상태 (10V 이상이면 true)
bool prevBatteryVoltageOK = false;    // 이전 배터리 전압 상태
unsigned long lastAutoControl = 0;    // 마지막 자동 제어 시간
bool autoControlEnabled = true;       // 자동 제어 활성화 여부

// Solar Power Monitoring Data (from VC_MON_LC)
float maxCurrent = 0.0;               // 최대 전류값 기록
float cumulativeEnergy = 0.0;         // 누적 전력량

// Serial Communication Variables
String inString = "0";
String command;
char command_char;

// RS232 Communication Variables for VC_MON_LC
String rs232Buffer = "";
String rs232Command = "";
bool rs232CommandReady = false;
unsigned long lastRS232Request = 0;
const unsigned long RS232_INTERVAL = 10000; // 10초마다 데이터 요청

// VC_MON_LC Data Structure
typedef struct {
  float voltage;      // 전압 (V)
  float current;      // 전류 (A) 
  float power;        // 전력 (W)
  float capacity;     // 용량 (Ah)
  float energy;       // 에너지 (Wh)
  bool dataValid;     // 데이터 유효성
} VCMonData;

VCMonData vcMonitor;



void setup() {
  // Digital Input Pins
  pinMode(PUSHBUTTON_GREEN_INPUT_PIN, INPUT_PULLUP);   // 녹색 푸시버튼 입력 (풀업 저항 사용)
  pinMode(PUSHBUTTON_RED_INPUT_PIN, INPUT_PULLUP);     // 적색 푸시버튼 입력 (풀업 저항 사용)

  // Digital Output Pins
  pinMode(PILOT_LAMP_GREEN_RED_OUTPUT_PIN, OUTPUT);    // 파일럿램프 녹/적(NO/NC)
  pinMode(FAN_COMMERCIAL_SMPS_OUTPUT_PIN, OUTPUT);     // 선풍기 부하(상용/SMPS)
  pinMode(FAN_BATTERY_MODULE_OUTPUT_PIN, OUTPUT);      // 선풍기 부하(이차전지모듈)
  pinMode(HALOGEN_LAMP_OUTPUT_PIN, OUTPUT);            // 할로겐램프

  // 시리얼 통신 설정
  Serial.begin(115200);   // USB 시리얼 (PC 통신용)
  Serial.setTimeout(50);
  
  Serial1.begin(9600);    // RS232 시리얼 (VC_MON_LC 통신용, D0/D1 핀)
  Serial1.setTimeout(100);
  
  // VC_MON_LC 데이터 초기화
  vcMonitor.voltage = 0.0;
  vcMonitor.current = 0.0;
  vcMonitor.power = 0.0;
  vcMonitor.capacity = 0.0;
  vcMonitor.energy = 0.0;
  vcMonitor.dataValid = false;
  
  // 초기화 메시지
  Serial.println("Arduino System with VC_MON_LC Initialized");
  Serial.println("RS232 Communication Ready on D0/D1");
}

void loop()
{
  // Push Button Input Reading
  greenButtonInput = digitalRead(PUSHBUTTON_GREEN_INPUT_PIN);
  redButtonInput = digitalRead(PUSHBUTTON_RED_INPUT_PIN);
  
  // Update Button States (LOW = pressed due to INPUT_PULLUP)
  GreenButtonState = (greenButtonInput == LOW) ? BUTTON_PRESSED : BUTTON_RELEASED;
  RedButtonState = (redButtonInput == LOW) ? BUTTON_PRESSED : BUTTON_RELEASED;
  
  // Battery Voltage Reading (ADC Values)
  battery1sVoltage = analogRead(BATTERY_1S_VOLTAGE_PIN);
  battery2sVoltage = analogRead(BATTERY_2S_VOLTAGE_PIN);
  battery3sVoltage = analogRead(BATTERY_3S_VOLTAGE_PIN);
  batteryTotalVoltage = analogRead(BATTERY_TOTAL_VOLTAGE_PIN);
  
  // Convert ADC values to actual voltages
  voltage1s_real = convertToVoltage(battery1sVoltage);
  voltage2s_real = convertToVoltage(battery2sVoltage);
  voltage3s_real = convertToVoltage(battery3sVoltage);
  voltageTotal_real = convertToVoltage(batteryTotalVoltage);

  // RS232 VC_MON_LC Communication Processing
  processRS232Communication();

  // Automatic System Control Processing
  if(autoControlEnabled && millis() - lastAutoControl > AUTO_CONTROL_INTERVAL)
  {
    processAutomaticControl();
    lastAutoControl = millis();
  }

  // Serial Communication Processing (USB)
  if(Serial.available())
  {
    inString = Serial.readStringUntil('e');

    if(inString.length() > 1)
    {
      int first = inString.indexOf("$");
      command = inString.substring(first+1, first+4);
      command_char = command.charAt(0);
    }
  }
  
  // Command Processing
  switch (command_char)
  {
    case 'a': // 파일럿램프 OFF (실제로는 적색 점등)
      PilotLampControl = PILOT_LAMP_OFF;
      Serial.println("Pilot Lamp OFF (RED ON - Hardware Limitation)");
      command = "";
      command_char = 0;
      break;
    case 'b': // 파일럿램프 GREEN
      PilotLampControl = PILOT_LAMP_GREEN;
      Serial.println("Pilot Lamp GREEN (NO Contact)");
      command = "";
      command_char = 0;
      break;
    case 'c': // 파일럿램프 RED
      PilotLampControl = PILOT_LAMP_RED;
      Serial.println("Pilot Lamp RED (NC Contact)");
      command = "";
      command_char = 0;
      break;
    case 'd': // 상용/SMPS 선풍기 ON
      FanCommercialControl = FAN_ON;
      Serial.println("Commercial Fan ON");
      command = "";
      command_char = 0;
      break;
    case 'e': // 상용/SMPS 선풍기 OFF
      FanCommercialControl = FAN_OFF;
      Serial.println("Commercial Fan OFF");
      command = "";
      command_char = 0;
      break;
    case 'f': // 이차전지모듈 선풍기 ON
      FanBatteryControl = FAN_ON;
      Serial.println("Battery Fan ON");
      command = "";
      command_char = 0;
      break;
    case 'g': // 이차전지모듈 선풍기 OFF
      FanBatteryControl = FAN_OFF;
      Serial.println("Battery Fan OFF");
      command = "";
      command_char = 0;
      break;
    case 'h': // 할로겐램프 ON
      HalogenLampControl = HALOGEN_LAMP_ON;
      Serial.println("Halogen Lamp ON");
      command = "";
      command_char = 0;
      break;
    case 'i': // 할로겐램프 OFF
      HalogenLampControl = HALOGEN_LAMP_OFF;
      Serial.println("Halogen Lamp OFF");
      command = "";
      command_char = 0;
      break;
    case 'j': // 배터리 전압 출력
      Serial.println("=== Battery Voltage Readings ===");
      Serial.print("1S Battery - ADC: ");
      Serial.print(battery1sVoltage);
      Serial.print(" | Voltage: ");
      Serial.print(voltage1s_real, 3);
      Serial.println("V");
      
      Serial.print("2S Battery - ADC: ");
      Serial.print(battery2sVoltage);
      Serial.print(" | Voltage: ");
      Serial.print(voltage2s_real, 3);
      Serial.println("V");
      
      Serial.print("3S Battery - ADC: ");
      Serial.print(battery3sVoltage);
      Serial.print(" | Voltage: ");
      Serial.print(voltage3s_real, 3);
      Serial.println("V");
      
      Serial.print("Total Battery - ADC: ");
      Serial.print(batteryTotalVoltage);
      Serial.print(" | Voltage: ");
      Serial.print(voltageTotal_real, 3);
      Serial.println("V");
      Serial.println("===============================");
      command = "";
      command_char = 0;
      break;
    case 'k': // VC_MON_LC 데이터 출력
      printVCMonitorData();
      command = "";
      command_char = 0;
      break;
    case 'l': // VC_MON_LC 데이터 리셋 (Clear)
      sendRS232Command("C");
      Serial.println("VC Monitor Data Reset Command Sent");
      command = "";
      command_char = 0;
      break;
    case 'm': // VC_MON_LC 자동 송신 시작
      sendRS232Command("S");
      Serial.println("VC Monitor Auto Send Start");
      command = "";
      command_char = 0;
      break;
    case 'n': // VC_MON_LC 자동 송신 정지
      sendRS232Command("P");
      Serial.println("VC Monitor Auto Send Stop");
      command = "";
      command_char = 0;
      break;
    case 'o': // A0 (1S) 전압 센서 읽기
      Serial.print("A0 (1S) - ADC: ");
      Serial.print(battery1sVoltage);
      Serial.print(" | Voltage: ");
      Serial.print(voltage1s_real, 3);
      Serial.println("V");
      command = "";
      command_char = 0;
      break;
    case 'p': // A1 (2S) 전압 센서 읽기
      Serial.print("A1 (2S) - ADC: ");
      Serial.print(battery2sVoltage);
      Serial.print(" | Voltage: ");
      Serial.print(voltage2s_real, 3);
      Serial.println("V");
      command = "";
      command_char = 0;
      break;
    case 'q': // A2 (3S) 전압 센서 읽기
      Serial.print("A2 (3S) - ADC: ");
      Serial.print(battery3sVoltage);
      Serial.print(" | Voltage: ");
      Serial.print(voltage3s_real, 3);
      Serial.println("V");
      command = "";
      command_char = 0;
      break;
    case 'r': // A3 (Total) 전압 센서 읽기
      Serial.print("A3 (Total) - ADC: ");
      Serial.print(batteryTotalVoltage);
      Serial.print(" | Voltage: ");
      Serial.print(voltageTotal_real, 3);
      Serial.println("V");
      command = "";
      command_char = 0;
      break;
    case 's': // 전압 센서 캘리브레이션 정보 출력
      printVoltageCalibrationInfo();
      command = "";
      command_char = 0;
      break;
    case 't': // 모든 전압 실시간 모니터링
      printAllVoltages();
      command = "";
      command_char = 0;
      break;
    case 'u': // 전체 시스템 상태 출력
      printSystemStatus();
      command = "";
      command_char = 0;
      break;
    case 'v': // 태양광 데이터 리셋
      maxCurrent = 0.0;
      cumulativeEnergy = 0.0;
      Serial.println("Solar Power Data Reset (Max Current, Cumulative Energy)");
      command = "";
      command_char = 0;
      break;
  }

  // Process Push Button Inputs
  processPushButtons();
  
  // Update All Output States
  updatePilotLampOutput();
  updateFanOutput();
  updateHalogenLampOutput();
}



// Output Control Functions
void updatePilotLampOutput()
{
  switch(PilotLampControl)
  {
    case PILOT_LAMP_OFF:
      // 현재 하드웨어로는 OFF 구현 불가 - 기본적으로 적색 표시
      digitalWrite(PILOT_LAMP_GREEN_RED_OUTPUT_PIN, LOW);   // 릴레이 OFF → NC 접점 → 적색 점등
      break;
    case PILOT_LAMP_GREEN:
      digitalWrite(PILOT_LAMP_GREEN_RED_OUTPUT_PIN, HIGH);  // 릴레이 ON → NO 접점 → 녹색 점등
      break;
    case PILOT_LAMP_RED:
      digitalWrite(PILOT_LAMP_GREEN_RED_OUTPUT_PIN, LOW);   // 릴레이 OFF → NC 접점 → 적색 점등
      break;
  }
}

void updateFanOutput()
{
  // Commercial/SMPS Fan Control
  digitalWrite(FAN_COMMERCIAL_SMPS_OUTPUT_PIN, (FanCommercialControl == FAN_ON) ? HIGH : LOW);
  
  // Battery Module Fan Control
  digitalWrite(FAN_BATTERY_MODULE_OUTPUT_PIN, (FanBatteryControl == FAN_ON) ? HIGH : LOW);
}

void updateHalogenLampOutput()
{
  digitalWrite(HALOGEN_LAMP_OUTPUT_PIN, (HalogenLampControl == HALOGEN_LAMP_ON) ? HIGH : LOW);
}

// Push Button Processing Functions
void processPushButtons()
{
  static bool prevGreenState = false;
  static bool prevRedState = false;
  
  // Edge detection for button presses
  bool greenPressed = (GreenButtonState == BUTTON_PRESSED && !prevGreenState);
  bool redPressed = (RedButtonState == BUTTON_PRESSED && !prevRedState);
  
  // 5. 할로겐 조명 동작 제어
  // 녹색 버튼이 눌렸을 때 - 할로겐 조명 ON
  if(greenPressed)
  {
    HalogenLampControl = HALOGEN_LAMP_ON;
    Serial.println("Green Button Pressed - Halogen Lamp ON");
  }
  
  // 적색 버튼이 눌렸을 때 - 할로겐 조명 OFF
  if(redPressed)
  {
    HalogenLampControl = HALOGEN_LAMP_OFF;
    Serial.println("Red Button Pressed - Halogen Lamp OFF");
  }
  
  // 두 버튼이 모두 눌렸을 때의 동작 (시스템 리셋)
  if(GreenButtonState == BUTTON_PRESSED && RedButtonState == BUTTON_PRESSED)
  {
    // 시스템 초기화
    HalogenLampControl = HALOGEN_LAMP_OFF;
    maxCurrent = 0.0;
    cumulativeEnergy = 0.0;
    
    Serial.println("Both Buttons Pressed - System Reset");
    Serial.println("- Halogen Lamp OFF");
    Serial.println("- Max Current Reset");
    Serial.println("- Cumulative Energy Reset");
  }
  
  // Update previous states
  prevGreenState = (GreenButtonState == BUTTON_PRESSED);
  prevRedState = (RedButtonState == BUTTON_PRESSED);
}

// RS232 VC_MON_LC Communication Functions
void processRS232Communication()
{
  // RS232 데이터 읽기
  if(Serial1.available())
  {
    rs232Buffer += Serial1.readString();
    
    // 완전한 메시지 확인 (CR 또는 LF로 끝나는지)
    if(rs232Buffer.indexOf('\r') >= 0 || rs232Buffer.indexOf('\n') >= 0)
    {
      parseVCMonitorData(rs232Buffer);
      rs232Buffer = ""; // 버퍼 클리어
    }
  }
  
  // 주기적으로 데이터 요청 (자동 모드가 아닐 때)
  if(millis() - lastRS232Request > RS232_INTERVAL)
  {
    requestVCMonitorData();
    lastRS232Request = millis();
  }
}

void sendRS232Command(String cmd)
{
  Serial1.print(cmd);
  Serial1.print('\r'); // CR 추가
  Serial1.flush();
}

void requestVCMonitorData()
{
  // VC_MON_LC에서 현재 데이터 요청
  sendRS232Command("R");
}

void parseVCMonitorData(String data)
{
  // VC_MON_LC 데이터 파싱
  // 예시 데이터: "100,498,24.01,0.00,1.59,0000000,5E"
  data.trim(); // 공백 제거
  
  if(data.length() > 10 && data.indexOf(',') > 0)
  {
    int commaIndex = 0;
    String values[7];
    int valueIndex = 0;
    
    // 콤마로 분리
    for(int i = 0; i < data.length() && valueIndex < 7; i++)
    {
      if(data.charAt(i) == ',' || i == data.length() - 1)
      {
        values[valueIndex] = data.substring(commaIndex, i);
        commaIndex = i + 1;
        valueIndex++;
      }
    }
    
    // 데이터 할당 (VC_MON_LC 매뉴얼 기준)
    if(valueIndex >= 5)
    {
      // values[0]: ID (무시)
      // values[1]: 상태 (무시)
      vcMonitor.voltage = values[2].toFloat() / 100.0;    // 전압 (0.01V 단위)
      vcMonitor.current = values[3].toFloat() / 1000.0;   // 전류 (0.001A 단위)
      vcMonitor.power = values[4].toFloat() / 100.0;      // 전력 (0.01W 단위)
      
      if(valueIndex >= 6)
      {
        vcMonitor.capacity = values[5].toFloat() / 1000.0; // 용량 (0.001Ah 단위)
      }
      
      vcMonitor.dataValid = true;
      
      // 1. 태양광발전 현황 모니터링 - 최대 전류 업데이트
      if(vcMonitor.current > maxCurrent)
      {
        maxCurrent = vcMonitor.current;
      }
      
      // 누적 전력량 계산 (간단한 적분 방식)
      static unsigned long prevTime = 0;
      unsigned long currentTime = millis();
      if(prevTime > 0)
      {
        float timeDelta = (currentTime - prevTime) / 1000.0 / 3600.0; // 시간 차이 (시간 단위)
        cumulativeEnergy += vcMonitor.power * timeDelta; // Wh 누적
      }
      prevTime = currentTime;
      
      Serial.print("VC_MON Data - V:");
      Serial.print(vcMonitor.voltage, 2);
      Serial.print("V, I:");
      Serial.print(vcMonitor.current, 3);
      Serial.print("A, P:");
      Serial.print(vcMonitor.power, 2);
      Serial.print("W, C:");
      Serial.print(vcMonitor.capacity, 3);
      Serial.println("Ah");
    }
  }
}

void printVCMonitorData()
{
  if(vcMonitor.dataValid)
  {
    Serial.println("=== VC_MON_LC Data ===");
    Serial.print("Voltage: ");
    Serial.print(vcMonitor.voltage, 2);
    Serial.println(" V");
    
    Serial.print("Current: ");
    Serial.print(vcMonitor.current, 3);
    Serial.println(" A");
    
    Serial.print("Power: ");
    Serial.print(vcMonitor.power, 2);
    Serial.println(" W");
    
    Serial.print("Capacity: ");
    Serial.print(vcMonitor.capacity, 3);
    Serial.println(" Ah");
    
    Serial.print("Energy: ");
    Serial.print(vcMonitor.energy, 2);
    Serial.println(" Wh");
    Serial.println("==================");
  }
  else
  {
    Serial.println("VC_MON_LC: No valid data available");
  }
}

// Voltage Sensor Functions
float convertToVoltage(int adcValue)
{
  // ADC 값을 실제 전압으로 변환
  // ADC 값 -> 아두이노 입력 전압 -> 실제 측정 전압
  float arduinoVoltage = (float)adcValue * (ARDUINO_REF_VOLTAGE / ADC_RESOLUTION);
  float actualVoltage = arduinoVoltage * VOLTAGE_SENSOR_RATIO;
  return actualVoltage;
}

void printVoltageCalibrationInfo()
{
  Serial.println("=== Voltage Sensor Calibration Info ===");
  Serial.print("Arduino Reference Voltage: ");
  Serial.print(ARDUINO_REF_VOLTAGE);
  Serial.println("V");
  
  Serial.print("ADC Resolution: ");
  Serial.print(ADC_RESOLUTION);
  Serial.println(" steps");
  
  Serial.print("Voltage Sensor Ratio: ");
  Serial.print(VOLTAGE_SENSOR_RATIO);
  Serial.println(":1");
  
  Serial.print("Voltage per ADC step: ");
  Serial.print((ARDUINO_REF_VOLTAGE * VOLTAGE_SENSOR_RATIO) / ADC_RESOLUTION, 6);
  Serial.println("V");
  
  Serial.print("Maximum measurable voltage: ");
  Serial.print(ARDUINO_REF_VOLTAGE * VOLTAGE_SENSOR_RATIO);
  Serial.println("V");
  Serial.println("=======================================");
}

void printAllVoltages()
{
  Serial.println("=== Real-time Voltage Monitor ===");
  Serial.print("A0 (1S):    ");
  Serial.print(voltage1s_real, 3);
  Serial.print("V (ADC: ");
  Serial.print(battery1sVoltage);
  Serial.println(")");
  
  Serial.print("A1 (2S):    ");
  Serial.print(voltage2s_real, 3);
  Serial.print("V (ADC: ");
  Serial.print(battery2sVoltage);
  Serial.println(")");
  
  Serial.print("A2 (3S):    ");
  Serial.print(voltage3s_real, 3);
  Serial.print("V (ADC: ");
  Serial.print(battery3sVoltage);
  Serial.println(")");
  
  Serial.print("A3 (Total): ");
  Serial.print(voltageTotal_real, 3);
  Serial.print("V (ADC: ");
  Serial.print(batteryTotalVoltage);
  Serial.println(")");
  Serial.println("=================================");
}

// Automatic System Control Functions
void processAutomaticControl()
{
  // 2. 이차전지 모듈 상태 모니터링 및 상태 판단
  prevBatteryVoltageOK = batteryVoltageOK;
  batteryVoltageOK = (voltageTotal_real >= BATTERY_THRESHOLD_VOLTAGE);
  
  // 상태 변경 시에만 로그 출력
  if(batteryVoltageOK != prevBatteryVoltageOK)
  {
    if(batteryVoltageOK)
    {
      Serial.print("Battery Status: OK (");
      Serial.print(voltageTotal_real, 2);
      Serial.println("V >= 10V)");
    }
    else
    {
      Serial.print("Battery Status: LOW (");
      Serial.print(voltageTotal_real, 2);
      Serial.println("V < 10V)");
    }
  }
  
  // 3. 부하(선풍기) 전원 제어
  controlFanPower();
  
  // 4. 파일럿램프 동작 제어
  controlPilotLamp();
}

void controlFanPower()
{
  // 3. 부하(선풍기) 전원 제어
  // 주의: 둘 중 하나만 ON되어야 함
  if(batteryVoltageOK)
  {
    // 10V 이상 - 이차전지모듈 전원 사용
    if(FanCommercialControl == FAN_ON)
    {
      FanCommercialControl = FAN_OFF;
      Serial.println("Switching from Commercial to Battery Power");
    }
    FanBatteryControl = FAN_ON;
  }
  else
  {
    // 10V 미만 - 상용전원 사용
    if(FanBatteryControl == FAN_ON)
    {
      FanBatteryControl = FAN_OFF;
      Serial.println("Switching from Battery to Commercial Power");
    }
    FanCommercialControl = FAN_ON;
  }
}

void controlPilotLamp()
{
  // 4. 파일럿램프 동작 제어
  if(batteryVoltageOK)
  {
    // 10V 이상 - 녹색 파일럿 램프 점등, 적색 소등
    if(PilotLampControl != PILOT_LAMP_GREEN)
    {
      PilotLampControl = PILOT_LAMP_GREEN;
      Serial.println("Pilot Lamp: GREEN ON, RED OFF (Battery ≥10V)");
    }
  }
  else
  {
    // 10V 미만 - 적색 파일럿 램프 점등, 녹색 소등
    if(PilotLampControl != PILOT_LAMP_RED)
    {
      PilotLampControl = PILOT_LAMP_RED;
      Serial.println("Pilot Lamp: RED ON, GREEN OFF (Battery <10V)");
    }
  }
}

// System Monitoring Functions
void printSystemStatus()
{
  Serial.println("=================== SYSTEM STATUS ===================");
  
  // 1. 태양광발전 현황
  if(vcMonitor.dataValid)
  {
    Serial.println("【1. Solar Power Status】");
    Serial.print("  Voltage: ");
    Serial.print(vcMonitor.voltage, 2);
    Serial.println(" V");
    
    Serial.print("  Current: ");
    Serial.print(vcMonitor.current, 3);
    Serial.println(" A");
    
    Serial.print("  Max Current: ");
    Serial.print(maxCurrent, 3);
    Serial.println(" A");
    
    Serial.print("  Power: ");
    Serial.print(vcMonitor.power, 2);
    Serial.println(" W");
    
    Serial.print("  Cumulative Energy: ");
    Serial.print(cumulativeEnergy, 3);
    Serial.println(" Wh");
  }
  else
  {
    Serial.println("【1. Solar Power Status】 - No Data Available");
  }
  
  // 2. 이차전지 모듈 상태
  Serial.println("【2. Battery Module Status】");
  Serial.print("  1S: ");
  Serial.print(voltage1s_real, 2);
  Serial.println(" V");
  
  Serial.print("  2S: ");
  Serial.print(voltage2s_real, 2);
  Serial.println(" V");
  
  Serial.print("  3S: ");
  Serial.print(voltage3s_real, 2);
  Serial.println(" V");
  
  Serial.print("  Total: ");
  Serial.print(voltageTotal_real, 2);
  Serial.print(" V (");
  Serial.print(batteryVoltageOK ? "OK" : "LOW");
  Serial.println(")");
  
  // 3. 부하 전원 제어 상태
  Serial.println("【3. Fan Power Control】");
  Serial.print("  Commercial Power: ");
  Serial.println(FanCommercialControl == FAN_ON ? "ON" : "OFF");
  Serial.print("  Battery Power: ");
  Serial.println(FanBatteryControl == FAN_ON ? "ON" : "OFF");
  
  // 4. 파일럿 램프 상태
  Serial.println("【4. Pilot Lamp Status】");
  Serial.print("  Status: ");
  if(PilotLampControl == PILOT_LAMP_GREEN) Serial.println("GREEN");
  else if(PilotLampControl == PILOT_LAMP_RED) Serial.println("RED");
  else Serial.println("OFF");
  
  // 5. 할로겐 조명 상태
  Serial.println("【5. Halogen Lamp Status】");
  Serial.print("  Status: ");
  Serial.println(HalogenLampControl == HALOGEN_LAMP_ON ? "ON" : "OFF");
  
  Serial.println("====================================================");
}