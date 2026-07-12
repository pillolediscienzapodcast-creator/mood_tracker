<script setup lang="ts"></script>

<template>
  <nav class="nav">
    <RouterLink to="/">Home</RouterLink>
    <RouterLink to="/mood">Mood</RouterLink>
  </nav>
  <RouterView />
</template>

<style scoped>
.nav {
  display: flex;
  gap: 1rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #eee;
}
</style>
