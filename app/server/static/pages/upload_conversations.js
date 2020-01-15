import Vue from 'vue';
import UploadConversations from '../components/upload_conversations.vue';

new Vue({
  el: '#mail-app',

  components: { UploadConversations },

  template: '<UploadConversations />',
});
