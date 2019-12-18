import Vue from 'vue';
import Conversations from '../components/conversations.vue';

Vue.use(require('vue-shortkey'), {
  prevent: ['input', 'textarea'],
});

new Vue({
  el: '#mail-app',

  components: { Conversations },

  template: '<Conversations />',
});
