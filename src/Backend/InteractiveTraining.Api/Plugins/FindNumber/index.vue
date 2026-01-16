<template>
    <div class="find-number-screen">
        <div class="header-bar">
            <h1 class="title">找数字规律</h1>
            <div class="phase-indicator">{{ phaseNames[currentPhase] }}</div>
            <div class="timer">{{ timeLeft }}</div>
        </div>
        
        <!-- Scatter Phase -->
        <div class="number-grid scatter" v-if="currentPhase === 'scatter' && gameActive">
             <div v-for="n in displayNumbers" :key="n" 
                  class="number-item"
                  :style="getScatterPosition(n)">
                 {{ n }}
             </div>
        </div>
        
        <!-- Quadrant Phase -->
        <div class="quadrant-container" v-if="currentPhase === 'quadrant' && gameActive">
            <div v-for="q in 4" :key="q" :class="['quadrant', 'q' + q]">
                <div v-for="n in getQuadrantNumbers(q)" :key="n" class="number-item">
                    {{ n }}
                </div>
            </div>
        </div>
        
        <!-- Row Phase -->
        <div class="row-container" v-if="currentPhase === 'row' && gameActive">
            <div v-for="(row, idx) in rowNumbers" :key="idx" class="number-row">
                <span v-for="n in row" :key="n" class="number-item">{{ n }}</span>
            </div>
        </div>
        
        <!-- Results Display -->
        <div class="stats" v-if="!gameActive">
            <h2>本轮结束</h2>
            <div class="result-info">
                <p class="missing-number">正确答案: <span>{{ missingNumber }}</span></p>
                <p>参与人数: {{ stats.totalUsers }}</p>
                <p>提交人数: {{ stats.totalSubmissions }}</p>
                <p>正确率: <span class="highlight">{{ stats.accuracy }}%</span></p>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';

const timeLeft = ref(30);
const currentPhase = ref('scatter');
const gameActive = ref(false);
const displayNumbers = ref([]);
const missingNumber = ref(42);
const stats = ref({
    totalUsers: 0,
    totalSubmissions: 0,
    accuracy: 0
});

const phaseNames = {
    scatter: '阶段一：散点模式',
    quadrant: '阶段二：象限模式',
    row: '阶段三：行序模式'
};

// Generate numbers 1-100 excluding missingNumber
const initNumbers = () => {
    const nums = [];
    for(let i=1; i<=100; i++) {
        if(i !== missingNumber.value) nums.push(i);
    }
    displayNumbers.value = nums;
};

// Scatter position (pseudo-random but stable)
const getScatterPosition = (n) => {
    const seed = n * 12345;
    return {
        left: ((seed % 90) + 5) + '%',
        top: (((seed * 7) % 70) + 15) + '%'
    };
};

// Quadrant numbers distribution
const getQuadrantNumbers = (quadrant) => {
    const perQuadrant = Math.ceil(displayNumbers.value.length / 4);
    const start = (quadrant - 1) * perQuadrant;
    const end = start + perQuadrant;
    return displayNumbers.value.slice(start, end);
};

// Row numbers (sorted in rows of ~10)
const rowNumbers = computed(() => {
    const rows = [];
    const sorted = [...displayNumbers.value].sort((a, b) => a - b);
    for(let i = 0; i < sorted.length; i += 10) {
        rows.push(sorted.slice(i, i + 10));
    }
    return rows;
});

let timerInterval;

// Listen for SignalR events from parent/host
const handleGameStart = (data) => {
    console.log('Large screen received game start:', data);
    if (data && data.missingNumber) {
        missingNumber.value = data.missingNumber;
    }
    gameActive.value = true;
    initNumbers();
    startTimer();
};

const handlePhaseChange = (data) => {
    console.log('Phase changed:', data);
    currentPhase.value = data.phase || 'scatter';
    if (data.missingNumber) {
        missingNumber.value = data.missingNumber;
    }
    gameActive.value = true;
    initNumbers();
    resetTimer();
    startTimer();
};

const handleStatsUpdate = (newStats) => {
    stats.value = newStats;
};

const handleGameEnd = (results) => {
    console.log('Game ended:', results);
    gameActive.value = false;
    missingNumber.value = results.missingNumber;
    stats.value = results.stats;
    clearInterval(timerInterval);
};

const startTimer = () => {
    clearInterval(timerInterval);
    timerInterval = setInterval(() => {
        if(timeLeft.value > 0) {
            timeLeft.value--;
        } else {
            clearInterval(timerInterval);
        }
    }, 1000);
};

const resetTimer = () => {
    timeLeft.value = 30;
};

onMounted(() => {
    // Listen to parent window for SignalR events
    if (window.parent && window.parent.signalRConnection) {
        const connection = window.parent.signalRConnection;
        connection.on('SwitchPlugin', handleGameStart);
        connection.on('PhaseChanged', handlePhaseChange);
        connection.on('StatsUpdate', handleStatsUpdate);
        connection.on('GameEnded', handleGameEnd);
    }
    
    // Default initialization for standalone testing
    initNumbers();
    gameActive.value = true;
    startTimer();
});

onUnmounted(() => {
    clearInterval(timerInterval);
    if (window.parent && window.parent.signalRConnection) {
        const connection = window.parent.signalRConnection;
        connection.off('SwitchPlugin', handleGameStart);
        connection.off('PhaseChanged', handlePhaseChange);
        connection.off('StatsUpdate', handleStatsUpdate);
        connection.off('GameEnded', handleGameEnd);
    }
});
</script>

<style scoped>
.find-number-screen {
    width: 100%;
    height: 100%;
    position: relative;
    background: radial-gradient(circle, #2b32b2 0%, #1488cc 100%);
    color: white;
    overflow: hidden;
}
.header-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 40px;
    background: rgba(0, 0, 0, 0.3);
}
.title {
    font-size: 36px;
    margin: 0;
}
.phase-indicator {
    font-size: 24px;
    color: #ffeb3b;
}
.timer {
    font-size: 64px;
    font-weight: bold;
    color: #ed7b2f;
    min-width: 100px;
    text-align: right;
}

/* Scatter Layout */
.number-grid.scatter {
    position: relative;
    width: 100%;
    height: calc(100% - 100px);
}
.number-grid.scatter .number-item {
    position: absolute;
    font-size: 28px;
    font-weight: bold;
    color: rgba(255, 255, 255, 0.9);
    text-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
    animation: float 3s ease-in-out infinite;
}

/* Quadrant Layout */
.quadrant-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
    height: calc(100% - 100px);
    gap: 2px;
    padding: 20px;
}
.quadrant {
    display: flex;
    flex-wrap: wrap;
    align-content: flex-start;
    gap: 15px;
    padding: 20px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 10px;
}
.quadrant .number-item {
    font-size: 24px;
    font-weight: bold;
}

/* Row Layout */
.row-container {
    padding: 40px;
    height: calc(100% - 100px);
    overflow-y: auto;
}
.number-row {
    display: flex;
    gap: 20px;
    margin-bottom: 20px;
    justify-content: center;
}
.number-row .number-item {
    font-size: 28px;
    font-weight: bold;
    padding: 10px 15px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
}

/* Stats/Results */
.stats {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(0, 0, 0, 0.9);
    padding: 50px 60px;
    border-radius: 20px;
    text-align: center;
    min-width: 400px;
}
.stats h2 {
    font-size: 48px;
    margin: 0 0 30px 0;
}
.result-info p {
    font-size: 28px;
    margin: 15px 0;
}
.missing-number span {
    font-size: 48px;
    color: #ffeb3b;
    font-weight: bold;
}
.highlight {
    color: #00a870;
    font-weight: bold;
}

@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}
</style>
