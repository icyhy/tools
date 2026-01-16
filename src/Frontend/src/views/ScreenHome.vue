<template>
  <div class="screen-home">
    <div v-if="currentPlugin" class="plugin-container">
      <component :is="pluginComponent" />
    </div>
    <div v-else class="standby-container">
      <div class="qrcode-section">
        <div class="header">
           <div class="logo">IT</div>
           <h1 class="title">互动培训平台</h1>
           <p class="subtitle">Interactive Training Platform</p>
        </div>
        
        <div class="qrcode-container">
            <div class="qrcode-placeholder">
            <!-- QR Code Placeholder -->
            <img :src="qrCodeUrl" alt="QR Code" />
            </div>
            <p class="guide-text">请使用手机扫描上方二维码加入互动</p>
            <p class="url-text">{{ mobileUrl }}</p>
        </div>
      </div>
      <div class="users-section">
        <h2>已签到人数: {{ userCount }}</h2>
        <div class="avatar-wall">
          <div v-for="user in users" :key="user.id" class="avatar">
            {{ user.name[0] }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, shallowRef } from 'vue';
import { connection, on, off } from '@/services/signalr';
import { loadPluginComponent } from '@/utils/pluginLoader';

const userCount = ref(0);
const users = ref([]);
const currentPlugin = ref(null);
const pluginComponent = shallowRef(null);
const mobileUrl = ref('');
const qrCodeUrl = ref('');

onMounted(() => {
  // Calculate dynamic URL
  const host = window.location.hostname;
  const port = window.location.port;
  const protocol = window.location.protocol;
  const baseUrl = `${protocol}//${host}:${port}`;
  
  mobileUrl.value = `${baseUrl}/mobile`;
  qrCodeUrl.value = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(mobileUrl.value)}`;

  on('UserJoined', (user) => {
    users.value.push({ id: Date.now(), name: 'User' });
    userCount.value++;
  });
  
  on('UserCountUpdate', (count) => {
      userCount.value = count;
  });

  on('SwitchPlugin', async (pluginId) => {
      console.log("Switching to plugin:", pluginId);
      currentPlugin.value = pluginId;
      try {
          const comp = await loadPluginComponent(`/plugins/${pluginId}/index.vue`);
          pluginComponent.value = comp;
      } catch (e) {
          console.error("Failed to load plugin", e);
      }
  });
});

onUnmounted(() => {
  off('UserJoined');
  off('UserCountUpdate');
  off('SwitchPlugin');
});
</script>

<style scoped>
.screen-home {
  height: 100%;
  width: 100%;
}
.standby-container {
  display: flex;
  height: 100%;
  width: 100%;
}
.plugin-container {
  width: 100%;
  height: 100%;
}
.qrcode-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  border-right: 1px solid #333;
  background-color: #1e1e1e;
}
.header {
    text-align: center;
    margin-bottom: 40px;
}
.logo {
    width: 80px;
    height: 80px;
    background: linear-gradient(135deg, #0052d9, #00a0e9);
    border-radius: 16px;
    margin: 0 auto 20px;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 32px;
    font-weight: bold;
    color: white;
}
.title {
    font-size: 36px;
    margin: 0;
    color: #fff;
}
.subtitle {
    font-size: 18px;
    color: #999;
    margin: 10px 0 0;
}
.qrcode-container {
    text-align: center;
    background: white;
    padding: 20px;
    border-radius: 16px;
}
.guide-text {
    margin-top: 20px;
    font-size: 18px;
    color: #333;
    font-weight: bold;
}
.url-text {
    margin-top: 10px;
    font-size: 14px;
    color: #666;
}
.users-section {
  flex: 2;
  padding: 40px;
}
.avatar-wall {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-top: 40px;
}
.avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background-color: #0052d9;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 24px;
  font-weight: bold;
}
</style>
