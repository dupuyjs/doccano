import Vue from 'vue';
import DownloadConversations from '../components/download_conversations.vue';

new Vue({
  el: '#mail-app',

  components: { DownloadConversations },

  template: '<DownloadConversations />',
});
