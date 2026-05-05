import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    redirect: "/synthesize",
  },
  {
    path: "/synthesize",
    name: "TextSynthesis",
    component: () => import("../views/TextSynthesis.vue"),
  },
  {
    path: "/voice-design",
    name: "VoiceDesign",
    component: () => import("../views/VoiceDesign.vue"),
  },
  {
    path: "/voice-clone",
    name: "VoiceClone",
    component: () => import("../views/VoiceClone.vue"),
  },
  {
    path: "/history",
    name: "History",
    component: () => import("../views/History.vue"),
  },
  {
    path: "/settings",
    name: "Settings",
    component: () => import("../views/Settings.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
