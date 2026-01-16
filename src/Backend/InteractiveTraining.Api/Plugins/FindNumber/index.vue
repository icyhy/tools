<template>
    <div class="find-number-screen">
        <h1 class="title">请找出缺失的数字</h1>
        <div class="timer">{{ timeLeft }}</div>
        
        <div class="number-grid" v-if="phase === 'scatter'">
             <div v-for="n in displayNumbers" :key="n" 
                  class="number-item"
                  :style="{ left: randomPos(n).x + '%', top: randomPos(n).y + '%' }">
                 {{ n }}
             </div>
        </div>
        
        <div class="stats" v-if="phase === 'result'">
            <h2>正确答案: {{ missingNumber }}</h2>
            <p>参与人数: {{ participantCount }}</p>
            <p>正确率: {{ accuracy }}%</p>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const timeLeft = ref(30);
const phase = ref('scatter'); // scatter, result
const displayNumbers = ref([]);
const missingNumber = ref(42); // Mock missing number
const participantCount = ref(0);
const accuracy = ref(0);

// Generate numbers 1-100 excluding missingNumber
const initNumbers = () => {
    const nums = [];
    for(let i=1; i<=100; i++) {
        if(i !== missingNumber.value) nums.push(i);
    }
    displayNumbers.value = nums;
};

const randomPos = (n) => {
    // Pseudo-random position based on number to keep it stable during render
    const seed = n * 12345;
    return {
        x: (seed % 90) + 5,
        y: ((seed * 7) % 80) + 10
    };
};

let timerInterval;

onMounted(() => {
    initNumbers();
    timerInterval = setInterval(() => {
        if(timeLeft.value > 0) {
            timeLeft.value--;
        } else {
            phase.value = 'result';
            clearInterval(timerInterval);
        }
    }, 1000);
});

onUnmounted(() => {
    clearInterval(timerInterval);
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
.title {
    text-align: center;
    padding-top: 20px;
    font-size: 48px;
    text-shadow: 0 0 10px rgba(0,0,0,0.5);
}
.timer {
    position: absolute;
    top: 20px;
    right: 40px;
    font-size: 80px;
    font-weight: bold;
    color: #ed7b2f;
}
.number-item {
    position: absolute;
    font-size: 32px;
    font-weight: bold;
    color: rgba(255, 255, 255, 0.8);
    transition: all 0.5s;
}
.stats {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(0,0,0,0.8);
    padding: 40px;
    border-radius: 20px;
    text-align: center;
    font-size: 32px;
}
</style>
