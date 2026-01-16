<template>
    <div class="find-number-mobile">
        <h2 class="prompt">{{ promptText }}</h2>
        
        <div class="input-area" v-if="!gameEnded">
            <input 
                type="tel" 
                v-model="answer" 
                maxlength="3" 
                class="number-input" 
                placeholder="?"
                @input="validateInput"
                :disabled="submitted"
            />
        </div>

        <button 
            v-if="!gameEnded"
            class="submit-btn" 
            @click="submitAnswer" 
            :disabled="!answer || submitted">
            {{ submitted ? '已提交' : '提交答案' }}
        </button>
        
        <p class="hint" v-if="submitted && !gameEnded">请关注大屏公布结果</p>
        
        <!-- Result Display -->
        <div v-if="gameEnded" class="result-panel">
            <h3>游戏结束</h3>
            <p class="correct-answer">正确答案: <span>{{ correctAnswer }}</span></p>
            <p v-if="yourScore !== null" :class="yourScore ? 'score-correct' : 'score-wrong'">
                {{ yourScore ? '✓ 回答正确!' : '✗ 回答错误' }}
            </p>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const answer = ref('');
const submitted = ref(false);
const gameEnded = ref(false);
const correctAnswer = ref(null);
const yourScore = ref(null);
const promptText = ref('请输入缺失的数字');

const validateInput = () => {
    answer.value = answer.value.replace(/[^0-9]/g, '');
};

const submitAnswer = async () => {
    if(!answer.value) return;
    
    try {
        // Get SignalR connection from parent frame
        if (window.parent && window.parent.signalRInvoke) {
            await window.parent.signalRInvoke('SubmitAnswer', 'FindNumber', parseInt(answer.value));
            console.log("Answer submitted via SignalR:", answer.value);
        } else {
            console.warn("SignalR not available, cannot submit answer");
        }
        
        submitted.value = true;
    } catch (err) {
        console.error("Failed to submit answer:", err);
        alert("提交失败，请重试");
    }
};

const handleGameEnd = (results) => {
    console.log('Mobile received game end:', results);
    gameEnded.value = true;
    correctAnswer.value = results.missingNumber;
    
    // Check if user's answer was correct
    if (submitted.value && answer.value) {
        yourScore.value = parseInt(answer.value) === results.missingNumber;
    }
};

const handlePhaseChange = (data) => {
    console.log('New phase started:', data);
    // Reset for new phase
    answer.value = '';
    submitted.value = false;
    gameEnded.value = false;
    correctAnswer.value = null;
    yourScore.value = null;
    promptText.value = '请输入缺失的数字';
};

const handleSubmissionConfirmed = (data) => {
    console.log('Submission confirmed:', data);
};

onMounted(() => {
    // Listen to parent window for SignalR events
    if (window.parent && window.parent.signalRConnection) {
        const connection = window.parent.signalRConnection;
        connection.on('GameEnded', handleGameEnd);
        connection.on('PhaseChanged', handlePhaseChange);
        connection.on('SubmissionConfirmed', handleSubmissionConfirmed);
    }
});

onUnmounted(() => {
    if (window.parent && window.parent.signalRConnection) {
        const connection = window.parent.signalRConnection;
        connection.off('GameEnded', handleGameEnd);
        connection.off('PhaseChanged', handlePhaseChange);
        connection.off('SubmissionConfirmed', handleSubmissionConfirmed);
    }
});
</script>

<style scoped>
.find-number-mobile {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding-top: 60px;
    min-height: 400px;
}
.prompt {
    font-size: 24px;
    margin-bottom: 40px;
    color: #333;
}
.number-input {
    font-size: 48px;
    text-align: center;
    width: 150px;
    padding: 10px;
    border: 2px solid #0052d9;
    border-radius: 10px;
    outline: none;
    letter-spacing: 5px;
}
.number-input:disabled {
    background: #f0f0f0;
    color: #999;
}
.submit-btn {
    margin-top: 40px;
    width: 80%;
    max-width: 300px;
    height: 50px;
    background-color: #0052d9;
    color: white;
    border: none;
    border-radius: 25px;
    font-size: 18px;
    font-weight: bold;
    cursor: pointer;
}
.submit-btn:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}
.hint {
    margin-top: 20px;
    color: #666;
    font-size: 14px;
}
.result-panel {
    text-align: center;
    padding: 30px;
    background: white;
    border-radius: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.result-panel h3 {
    font-size: 28px;
    margin-bottom: 20px;
    color: #333;
}
.correct-answer {
    font-size: 20px;
    color: #666;
    margin: 15px 0;
}
.correct-answer span {
    font-size: 48px;
    color: #0052d9;
    font-weight: bold;
    display: block;
    margin-top: 10px;
}
.score-correct {
    font-size: 24px;
    color: #00a870;
    font-weight: bold;
    margin-top: 20px;
}
.score-wrong {
    font-size: 24px;
    color: #e34d59;
    font-weight: bold;
    margin-top: 20px;
}
</style>
