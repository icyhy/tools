<template>
  <div class="mobile-login">
    <div class="logo-area">
      <h1>互动培训</h1>
    </div>
    
    <div class="role-selector">
      <button 
        class="role-btn" 
        :class="{ active: role === 'participant' }"
        @click="role = 'participant'"
      >
        我是参与者
      </button>
      <button 
        class="role-btn" 
        :class="{ active: role === 'host' }"
        @click="role = 'host'"
      >
        我是主持人
      </button>
    </div>

    <div class="form-area" v-if="role === 'participant'">
      <input v-model="name" placeholder="请输入您的姓名" class="input-field" />
      <button @click="handleLogin" class="btn-primary" :disabled="!name">加入互动</button>
    </div>

    <div class="form-area" v-if="role === 'host'">
      <input v-model="hostPassword" type="password" placeholder="请输入主持人密码" class="input-field" />
      <button @click="handleHostLogin" class="btn-primary" :disabled="!hostPassword">进入控制台</button>
      <p v-if="loginError" class="error-msg">{{ loginError }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { invoke, on, off } from '@/services/signalr';

const router = useRouter();
const role = ref('participant');
const name = ref('');
const hostPassword = ref('');
const loginError = ref('');

const handleLogin = async () => {
  if (!name.value) return;
  
  localStorage.setItem('userName', name.value);
  localStorage.setItem('userRole', 'participant');
  
  try {
      console.log("Attempting to join session with name:", name.value);
      // Call JoinSession to notify server
      await invoke("JoinSession", name.value);
      console.log("JoinSession success, navigating to lobby");
      router.push('/mobile/lobby');
  } catch (err) {
      console.error("Join session failed", err);
      alert("无法连接到服务器");
  }
};

const handleHostLogin = async () => {
    if(!hostPassword.value) return;
    
    // Listen for auth result
    const onSuccess = () => {
        cleanup();
        localStorage.setItem('userRole', 'host');
        router.push('/mobile/host');
    };
    
    const onFail = () => {
        cleanup();
        loginError.value = "密码错误";
    };
    
    const cleanup = () => {
        off("HostAuthSuccess");
        off("HostAuthFailed");
    };
    
    on("HostAuthSuccess", onSuccess);
    on("HostAuthFailed", onFail);
    
    try {
        await invoke("JoinHost", hostPassword.value);
    } catch (err) {
        cleanup();
        console.error(err);
        loginError.value = "连接失败";
    }
};
</script>

<style scoped>
.mobile-login {
  padding: 40px 20px;
  text-align: center;
}
.logo-area {
  margin-bottom: 40px;
}
.role-selector {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-bottom: 30px;
}
.role-btn {
    padding: 10px 20px;
    border: 1px solid #ddd;
    border-radius: 20px;
    background: white;
    color: #666;
    font-size: 14px;
}
.role-btn.active {
    background: #0052d9;
    color: white;
    border-color: #0052d9;
}
.input-field {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 16px;
  box-sizing: border-box;
}
.btn-primary {
  width: 100%;
  padding: 12px;
  background-color: #0052d9;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
}
.error-msg {
    color: red;
    margin-top: 10px;
    font-size: 14px;
}
</style>
