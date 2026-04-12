# 📱 OpenGuy Mobile App Setup Guide

Complete guide for building and deploying the React Native mobile app for OpenGuy robot control.

---

## Quick Start

### 1. Prerequisites
- **Node.js** 16+ and npm
- **React Native** environment setup
- **Android Studio** or **Xcode** (depending on target platform)
- **OpenGuy Backend** running (local or cloud)

---

## iOS Setup (macOS only)

### 1. Install Dependencies
```bash
cd mobile
npm install

# Install CocoaPods dependencies
cd ios
pod install
cd ..
```

### 2. Build and Run
```bash
# Start Metro bundler
npm start

# In another terminal, run on iOS simulator
npm run ios

# Or run on physical device
npm run ios -- --device "Device Name"
```

### 3. Build for Release
```bash
react-native build-ios

# Or using Xcode
cd ios
xcodebuild -workspace OpenGuy.xcworkspace -scheme OpenGuy -configuration Release
```

### 4. Deploy to App Store
```bash
# Archive for App Store
cd ios
xcodebuild -workspace OpenGuy.xcworkspace -scheme OpenGuy -configuration Release -archivePath build/OpenGuy.xcarchive archive

# Export for distribution
xcodebuild -exportArchive -archivePath build/OpenGuy.xcarchive -exportPath build/Export -exportOptionsPlist exportOptions.plist
```

### Troubleshooting iOS
```bash
# Clear cache
rm -rf node_modules
npm install
cd ios && pod install && cd ..

# Reset Metro cache
npm start -- --reset-cache

# Clear Xcode build folder
cd ios && xcodebuild clean -workspace OpenGuy.xcworkspace && cd ..
```

---

## Android Setup

### 1. Install Dependencies
```bash
cd mobile
npm install
```

### 2. Setup Android Environment
```bash
# Set ANDROID_HOME
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/tools
export PATH=$PATH:$ANDROID_HOME/tools/bin
export PATH=$PATH:$ANDROID_HOME/platform-tools

# Add to ~/.zshrc or ~/.bash_profile for persistence
echo 'export ANDROID_HOME=$HOME/Library/Android/sdk' >> ~/.zshrc
```

### 3. Build and Run
```bash
# Start Metro bundler
npm start

# In another terminal, run on Android
npm run android

# Or with specific device
npm run android -- --deviceId emulator-5554
```

### 4. Build for Release
```bash
# Generate signing key (one time only)
cd android/app
keytool -genkey -v -keystore release.keystore -keyalg RSA -keysize 2048 -validity 10000 -alias openguy

# Build APK
cd ../..
./android/gradlew.bat app:assembleRelease

# Build AAB (for Play Store)
./android/gradlew.bat app:bundleRelease
```

### 5. Deploy to Play Store
```bash
# Sign Android App Bundle
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 \
  -keystore android/app/release.keystore \
  android/app/build/outputs/bundle/release/app-release.aab alias_name

# Verify signing
zipinfo -1 android/app/build/outputs/bundle/release/app-release.aab | grep -c "\.so"

# Upload to Play Store via Google Play Console web interface
# Or using FastLane (see below)
```

### Troubleshooting Android
```bash
# Start emulator
emulator -avd Pixel_4_API_30

# List devices
adb devices

# Clear Android cache
cd android && ./gradlew clean && cd ..

# View Android logs
adb logcat -s ReactNativeJS

# Reinstall app
adb uninstall com.openguy
npm run android
```

---

## Cross-Platform Configuration

### Update API Endpoint
Edit `RobotControlScreen.js`:
```javascript
const [apiUrl, setApiUrl] = useState('http://your-backend.com');
```

Or set at runtime in the app settings.

### Configure Bots
```javascript
// WhatsApp
const [botType, setBotType] = useState('whatsapp');
const [phoneNumber, setPhoneNumber] = useState('+1234567890');

// Telegram
const [botType, setBotType] = useState('telegram');
const [telegramChatId, setTelegramChatId] = useState('123456789');

// Direct API
const [botType, setBotType] = useState('api');
```

### Voice Recognition
App includes voice control via React Native Voice:
```javascript
// Start listening
await Voice.start('en-US');

// Stop listening
await Voice.stop();

// Results automatically update command input
```

---

## Production Deployment

### iOS App Store
1. Create Apple Developer account ($99/year)
2. Create App ID in Apple Developer portal
3. Create certificate and provisioning profile
4. Build archive
5. Upload via Xcode or Transporter
6. Submit for review

### Android Play Store
1. Create Google Play Developer account ($25 one-time)
2. Create app in Google Play Console
3. Build signed AAB
4. Upload to beta/production track
5. Fill out store listing
6. Submit for review

### Fastlane Automation
```bash
# Install Fastlane
sudo gem install fastlane -NV

# Initialize for iOS
cd ios
fastlane init

# Initialize for Android
cd android
fastlane init

# Deploy iOS
cd ios
fastlane release

# Deploy Android
cd android
fastlane release
```

---

## App Features

### 🎤 Voice Control
```javascript
// Tap "🎤 Listen" button
// Speak your command: "move forward 10 centimeters"
// Command auto-populated, tap "▶️ Execute"
```

### 🤖 Robot Status
Real-time display of:
- Robot mode (Hardware/Simulator)
- Current position
- Facing angle
- Success rate (via learning system)
- Command history

### 🧠 Learning Feedback
Shows:
- Robot's learned strategies
- Success rates
- Most common failures
- Confidence scores

### 🔄 Multi-Bot Support
Switch between:
- **Direct API:** Direct connection to backend
- **WhatsApp:** Via Twilio (uses your WhatsApp number)
- **Telegram:** Via Telegram Bot API

### ⚡ Quick Commands
Pre-defined buttons for:
- move forward
- rotate right
- grab
- release
- move backward
- status

### 📜 Command History
View last 10 commands with:
- Original command text
- Parsed action
- Execution timestamp
- Success/failure status

---

## Network Configuration

### Local Development
```javascript
// Connect to local backend
const apiUrl = 'http://192.168.1.100:5000';  // Your machine IP
```

### Cloud Backend
```javascript
// Connect to Heroku
const apiUrl = 'https://openguy-robot.herokuapp.com';

// Connect to AWS
const apiUrl = 'https://openguy.elasticbeanstalk.com';
```

### SSL/HTTPS
App automatically handles:
- Self-signed certificates (enable in dev mode)
- Certificate pinning (can be configured)
- HTTPS connections

---

## Debugging

### Debug Mode
```bash
# Enable React Native debugger
npm install --save-dev react-native-debugger

# Launch debugger
react-native-debugger
```

### Logging
```javascript
// View console logs
console.log('Debug message');

// View network requests
axios.interceptors.response.use(response => {
  console.log('API Response:', response.data);
  return response;
});
```

### Device Logs
```bash
# iOS
xcrun simctl spawn booted log stream --predicate 'process == "RobotControl"'

# Android
adb logcat -s RobotControl
```

---

## Testing

### Unit Tests
```bash
npm test
```

### Integration Tests
```bash
# Test with backend mock
npm run test:integration
```

### Manual Testing Checklist
- [ ] Voice input works
- [ ] Command execution succeeds
- [ ] Robot status updates
- [ ] Learning data displays
- [ ] History logs correctly
- [ ] Quick commands work
- [ ] Bot switching works (WhatsApp/Telegram/API)
- [ ] Network errors handled gracefully
- [ ] App doesn't crash on invalid input

---

## Performance Optimization

### Bundle Size
```bash
# Check bundle size
npm run build-javascript

# Analyze bundle
npm install --save-dev react-native-bundle-visualizer
```

### Memory Usage
- Limit history to last 10 commands
- Clean up voice listener on unmount
- Debounce API calls
- Cache learning data

### Network Performance
- Use compression for API calls
- Implement request retry logic
- Queue commands during offline
- Batch multiple commands

---

## App Store Submission

### iOS Requirements
- Privacy policy URL
- Screenshots (2-5 per supported device)
- Description and keywords
- Keywords
- Support URL
- Marketing URL

### Android Requirements
- High-res icon (512x512)
- Screenshots (2-8)
- Graphic assets (1024x500)
- Description and short description
- Privacy policy

---

## Development Workflow

### Branch Strategy
```bash
main          # Production releases
├─ develop    # Integration branch
├─ feature/*  # New features
└─ bugfix/*   # Bug fixes
```

### Commit Convention
```
[TYPE] - Description

Types: feat, fix, docs, style, refactor, test, ci, chore
```

### Version Numbering
```
1.0.0
↓ ↓ ↓
major.minor.patch

1.0.0-beta.1  # Pre-release
1.0.0+build1  # Build metadata
```

---

## Files Structure

```
mobile/
├── RobotControlScreen.js    # Main screen component
├── package.json             # Dependencies
├── ios/                     # iOS-specific files
│   ├── OpenGuy.xcodeproj/
│   └── Podfile
├── android/                 # Android-specific files
│   ├── app/
│   └── gradle.properties
├── __tests__/               # Unit tests
└── babel.config.js          # Babel configuration
```

---

## Common Issues & Solutions

### Issue: Metro bundler crashes
```bash
# Solution
npm start -- --reset-cache
```

### Issue: Voice recognition not working
```bash
# Ensure microphone permissions granted
# On Android: Settings > Apps > OpenGuy > Permissions > Microphone
# On iOS: Settings > Privacy > Microphone > OpenGuy: ON
```

### Issue: Network timeouts
```javascript
// Increase timeout in axios
axios.defaults.timeout = 30000; // 30 seconds
```

### Issue: Android build fails
```bash
# Clear gradle cache
cd android
./gradlew clean
cd ..
npm run android
```

### Issue: iOS pod issues
```bash
cd ios
rm -rf Pods Podfile.lock
pod install
cd ..
```

---

## Next Steps

1. **Setup Environment:** Install Node, React Native CLI
2. **Clone/Pull Code:** Get mobile app code
3. **Install Dependencies:** `npm install`
4. **Configure Backend:** Set API endpoint
5. **Run Locally:** `npm run ios` or `npm run android`
6. **Test Features:** Try voice, status, history
7. **Build Release:** Create signed binary
8. **Deploy:** Submit to App Store/Play Store

---

## Support

For issues or questions:
- Check console logs
- Enable debug mode
- Review network requests
- Test with local backend first
- File issue on GitHub

---

Built with ❤️ for OpenGuy Mobile
