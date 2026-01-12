<script setup lang="ts">
import { toast } from '@/composables/useToast'
import Toast from './Toast.vue'
</script>

<template>
  <Teleport to="body">
    <div class="toast-container">
      <TransitionGroup name="toast">
        <Toast
          v-for="item in toast.toasts"
          :key="item.id"
          :message="item.message"
          :type="item.type"
          :visible="item.visible"
          @close="toast.hide(item.id)"
        />
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-container {
  position: fixed;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 90%;
  width: 360px;
  pointer-events: none;
}

.toast-container > * {
  pointer-events: auto;
}

/* Toast transition animations */
.toast-enter-active {
  transition: all 0.3s ease-out;
}

.toast-leave-active {
  transition: all 0.2s ease-in;
}

.toast-enter-from {
  opacity: 0;
  transform: translateY(-20px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.toast-move {
  transition: transform 0.3s ease;
}
</style>
