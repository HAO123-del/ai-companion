<script setup lang="ts">
import { RouterView } from 'vue-router'
import ToastContainer from '@/components/ToastContainer.vue'
</script>

<template>
  <div class="mobile-container">
    <RouterView v-slot="{ Component, route }">
      <Transition :name="(route.meta.transition as string) || 'fade'" mode="out-in">
        <component :is="Component" :key="route.path" />
      </Transition>
    </RouterView>
    <ToastContainer />
  </div>
</template>

<style>
/* Fade transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Slide left transition (for forward navigation) */
.slide-left-enter-active,
.slide-left-leave-active {
  transition: transform 0.2s ease-out, opacity 0.2s ease-out;
  will-change: transform, opacity;
}

.slide-left-enter-from {
  transform: translate3d(20px, 0, 0);
  opacity: 0;
}

.slide-left-leave-to {
  transform: translate3d(-20px, 0, 0);
  opacity: 0;
}

/* Slide right transition (for back navigation) */
.slide-right-enter-active,
.slide-right-leave-active {
  transition: transform 0.2s ease-out, opacity 0.2s ease-out;
  will-change: transform, opacity;
}

.slide-right-enter-from {
  transform: translate3d(-20px, 0, 0);
  opacity: 0;
}

.slide-right-leave-to {
  transform: translate3d(20px, 0, 0);
  opacity: 0;
}

/* Slide up transition (for modals/overlays) */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.25s ease-out, opacity 0.25s ease-out;
  will-change: transform, opacity;
}

.slide-up-enter-from {
  transform: translate3d(0, 100%, 0);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translate3d(0, 100%, 0);
  opacity: 0;
}
</style>
