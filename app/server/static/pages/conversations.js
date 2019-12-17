import Vue from 'vue';
import Conversations from '../components/conversations.vue';

Vue.use(require('vue-shortkey'));

new Vue({
  el: '#mail-app',

  components: { Conversations },

  template: '<Conversations />',
});
