---
name: Training Platform Complete Workflow Test
description: Complete end-to-end testing workflow for the interactive training platform, covering sign-in, game launch, user participation, and results display across multiple browser windows
---

# Training Platform Complete Workflow Test

This skill provides a systematic approach to testing the complete workflow of the interactive training platform.

## Prerequisites

- Training platform server running on `http://localhost:8000`
- Three separate browser windows/sessions (Display, Host, User)
- Default credentials: Host password = `admin123`, Admin password = `admin123`

## Test Workflow

### Phase 1: Environment Setup

**Objective**: Open three independent browser windows for Display, Host, and User

1. **Window 1 - Display Screen**
   - Navigate to `http://localhost:8000/`
   - Should show: Training title, QR code, participant count
   - Keep this window open throughout the test

2. **Window 2 - Host Control**
   - Navigate to `http://localhost:8000/signin` or use different origin like `http://0.0.0.0:8000/signin`
   - Fill in form:
     - Name: "主持人测试" (or any host name)
     - Role: Select "主持人"
     - Password: `admin123`
   - Click "签到进入"
   - Should redirect to host control page showing available plugins

3. **Window 3 - Regular User**
   - Navigate to `http://localhost:8000/signin` (use different origin if needed to avoid session conflict)
   - Fill in form:
     - Name: "用户A" (or any user name)
     - Department: "技术部" (optional)
     - Role: "普通用户" (default)
   - Click "签到进入"
   - Should redirect to user home page

**Validation**:
- ✅ Display window shows updated participant count (2 or more)
- ✅ Host window shows "你好，[主持人名字]"
- ✅ User window shows "你好，[用户名字]"

---

### Phase 2: Sign-in Real-time Updates

**Objective**: Verify real-time participant count updates

1. **Check Display Window**
   - Observe participant count: "已签到: X 人"
   - Should increment as users sign in

2. **Test WebSocket Connection**
   - Open browser console on Display window
   - Check for WebSocket connection messages
   - Verify no connection errors

**Validation**:
- ✅ Participant count updates without manual refresh
- ✅ WebSocket connection is established (`/ws/display`)

---

### Phase 3: Launch Interactive Game

**Objective**: Start a game from Host and verify Display switches to game view

1. **Host Actions**
   - Click "进入【找数字规律】控制台"
   - Should navigate to plugin control page
   - Click "开始第1阶段" button

2. **Display Verification** ⚠️ CRITICAL
   - **Expected**: Display window should automatically reload and show game grid
   - **Check**: Does it show numbers or still showing QR code?
   - If not automatic, manually navigate to `http://localhost:8000/display/find_numbers` as workaround

3. **User Verification**
   - User window should show:
     - Input fields for missing numbers
     - "提交答案" button
   - If not, click "进入【找数字规律】" from user home

**Validation**:
- ✅ Host console shows current phase and controls
- ⚠️ Display AUTO-SWITCHES to game view (this is the key feature to test)
- ✅ User sees interactive input fields

---

### Phase 4: User Participation

**Objective**: Test user answer submission

1. **User Actions**
   - Observe numbers on Display window
   - Identify missing numbers in the pattern
   - Enter answers in input fields (e.g., 3, 16, 33)
   - Click "提交答案" button

2. **Verification**
   - Should show "已提交" message
   - Host console may show submission count (if implemented)

**Validation**:
- ✅ Answer submission succeeds
- ✅ User sees confirmation message

---

### Phase 5: Game Progression

**Objective**: Test phase transitions controlled by Host

1. **Host Actions**
   - Switch phases:
     - Click "开始第2阶段" → Display should update to 4-quadrant layout
     - Click "开始第3阶段" → Display should update to ordered grid
   - Click "结束本轮" button

2. **Display Verification**
   - Verify Display updates with each phase change
   - Numbers should rearrange according to phase pattern

**Validation**:
- ✅ Phase 2 shows 4-quadrant layout
- ✅ Phase 3 shows ordered grid
- ✅ Phase transitions are smooth

---

### Phase 6: Results Display

**Objective**: Verify result statistics are correct

1. **Check Display Window**
   - Should show "本轮结果"
   - **Correct answers**: List of numbers
   - **参与人数**: Should be > 0 (number of users who submitted)
   - **整体准确率**: Should be calculated percentage

2. **Check User Window**
   - Should show correct answers
   - May show "你找对了 X 个数字"

**Validation**:
- ⚠️ Participant count is accurate (not 0)
- ⚠️ Accuracy percentage is calculated correctly
- ✅ Correct answers are displayed

---

### Phase 7: Reset and Repeat

**Objective**: Test multiple rounds

1. **Host Actions**
   - Click "重置" or start a new round
   - Repeat from Phase 3

**Validation**:
- ✅ System can handle multiple rounds
- ✅ Data doesn't carry over incorrectly

---

## Common Issues and Solutions

### Issue 1: Display Not Auto-Switching to Game

**Symptom**: Display shows QR code even after Host starts game

**Workaround**:
- Manually navigate to `http://localhost:8000/display/find_numbers`

**Root Cause**:
- WebSocket `plugin_start` message not being received/handled
- Check browser console for WebSocket errors
- Verify `mobile.py` broadcasts the message
- Verify `index.html` handles `plugin_start` event

### Issue 2: Participant Count = 0 in Results

**Symptom**: Results show "参与人数: 0" even though users submitted

**Root Cause**:
- Data not being saved to database
- Plugin `handle_input` function not working
- Results query logic issue

**Debug Steps**:
- Check server logs during answer submission
- Verify database has submission records
- Check plugin results calculation logic

### Issue 3: Session Conflicts Across Windows

**Symptom**: Signing in as Host overwrites User session

**Solution**:
- Use different origins:
  - Display: `http://localhost:8000/`
  - Host: `http://0.0.0.0:8000/` or `http://127.0.0.1:8000/`
  - User: `http://localhost:8000/`
- Browsers treat different domains as separate sessions

### Issue 4: IP Address Not Accessible

**Symptom**: QR code shows IP that can't be accessed from mobile

**Solution**:
- Set environment variable: `export SERVER_IP=192.168.1.x`
- Or modify code to use correct local network IP
- Use `ifconfig | grep inet` to find correct IP

---

## Success Criteria

A successful complete workflow test should achieve:

- ✅ All three windows open and authenticate properly
- ✅ Participant count updates in real-time
- ✅ **Display AUTO-SWITCHES to game when Host starts (CRITICAL)**
- ✅ User can submit answers successfully
- ✅ Host can control game phases
- ✅ **Results show correct participant count and accuracy (CRITICAL)**
- ✅ Multiple rounds work without issues

---

## Notes

- **Browser Compatibility**: Tested with Chrome/Chromium
- **Network**: Works on localhost; IP access may require network configuration
- **Performance**: Designed for 10-50 concurrent users
- **Data Persistence**: Uses SQLite database in `app.db`

---

## Quick Test Command

For automated testing, see `test/complete-workflow.spec.js` (if exists)
