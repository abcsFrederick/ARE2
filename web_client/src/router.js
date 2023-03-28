import Vue from 'vue'
import Router from 'vue-router'
import Home from './views/homepage'
import Workflow1 from './views/workflow1'

Vue.use(Router)

const routes = [
  {
    path: "/",
    name: "ARE2",
    component: Home,
  },
  {
    path: "/workflow1",
    name: "workflow1",
    component: Workflow1,
    props: true
  }
];

const router = new Router({
  routes,
});

export default router;