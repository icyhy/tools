<template>
    <div class="find-number-mobile">
        <h2 class="prompt">请输入缺失的数字</h2>
        
        <div class="input-area">
            <input 
                type="tel" 
                v-model="answer" 
                maxlength="3" 
                class="number-input" 
                placeholder="?"
                @input="validateInput"
            />
        </div>

        <button 
            class="submit-btn" 
            @click="submitAnswer" 
            :disabled="!answer || submitted">
            {{ submitted ? '已提交' : '提交答案' }}
        </button>
        
        <p class="hint" v-if="submitted">请关注大屏公布结果</p>
    </div>
</template>

<script setup>
import { ref } from 'vue';

const answer = ref('');
const submitted = ref(false);

const validateInput = () => {
    answer.value = answer.value.replace(/[^0-9]/g, '');
};

const submitAnswer = async () => {
    if(!answer.value) return;
    
    // In real app, call SignalR here
    console.log("Submitting answer:", answer.value);
    
    submitted.value = true;
};
</script>

<style scoped>
.find-number-mobile {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding-top: 60px;
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
.submit-btn {
    margin-top: 40px;
    width: 80%;
    height: 50px;
    background-color: #0052d9;
    color: white;
    border: none;
    border-radius: 25px;
    font-size: 18px;
    font-weight: bold;
}
.submit-btn:disabled {
    background-color: #ccc;
}
.hint {
    margin-top: 20px;
    color: #666;
}
</style>
