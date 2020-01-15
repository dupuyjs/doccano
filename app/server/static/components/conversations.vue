<template lang="pug">
extends ./conversations.pug


block annotation-area
  corrector(
    v-if="docs[pageNumber] && annotations[pageNumber]"
    :text="docs[pageNumber].text"
    :doc="docs[pageNumber]"
    :start="docs[pageNumber].startTimeInSeconds"
    :end="docs[pageNumber].endTimeInSeconds"
    :audioFile="conversation.audioFile"
    :labels="labels"
    :entity-positions="annotations[pageNumber]"
    :search-query="searchQuery"
    :key="selectedConversationId"
    @dataChanged="getCorrectedText"
    @remove-label="removeLabel"
    @ignore-document="ignoreDocument"
    @approve-document-correction="approveDocumentCorrection"
    @approve-document-annotations="approveDocumentAnnotations"
    @add-label="addLabel"
    @update-label="updateLabel"
    ref="corrector"
  )

</template>

<style scoped>
.card-header-title {
  padding: 1.5rem;
}
</style>

<script>
import annotationMixin from './annotationMixin';
import Corrector from './corrector.vue';

import HTTP from './http';

export default {

  data() {
    return {
      conversations: [],
      selectedConversationId: 0,
      correctedText: '',
      ordering: 'created_at',
    };
  },
  components: { Corrector },
  mixins: [annotationMixin],
  computed: {
    conversation() {
      return this.conversations.find(c => c.id === this.selectedConversationId);
    },
    documentIsCorrected() {
      const document = this.docs[this.pageNumber];
      return document != null && document.isValidated;
    },
    approveDocumentCorrectionTooltip() {
      return this.documentIsCorrected
        ? 'Correction done, click to correct transcript'
        : 'Click to correct transcript';
    },
  },
  methods: {
    addLabel(annotation) {
      const docId = this.docs[this.pageNumber].id;
      HTTP.post(`docs/${docId}/annotations`, annotation).then((response) => {
        this.annotations[this.pageNumber].push(response.data);
      });
    },
    async updateLabel(annotation) {
      const docId = this.docs[this.pageNumber].id;
      await HTTP.put(`docs/${docId}/annotations/${annotation.id}`, annotation);
    },
    async ignoreDocument() {
      const doc = this.docs[this.pageNumber];
      doc.isIgnored = !doc.isIgnored;
      await HTTP.put(`docs/${doc.id}`, doc);
    },
    async submit() {
      if (this.selectedConversationId > 0) {
        const state = this.getState();
        this.url = `docs?q=${this.searchQuery}&conversation=${this.selectedConversationId}&seq_annotations__isnull=${state}&offset=${this.offset}&ordering=${this.ordering}`;
        await this.search();
        this.pageNumber = 0;
      }
    },
    parseConversationsTitle(conversation) {
      const c = JSON.parse(conversation.metadata);
      if (c.service !== undefined) {
        return c.service;
      }
      return `Conversation ${c.id}`;
    },
    getCorrectedText(text) {
      this.correctedText = text;
    },
    async approveDocumentCorrection() {
      const document = this.docs[this.pageNumber];
      if (!this.documentIsCorrected) {
        // Edit mode
        const correctedText = this.$refs.corrector.getText();
        await HTTP.post(`docs/${document.id}/approve-correction`, { corrected: true, correctedText });
        document.text = correctedText;
      } else {
        // Not-edit mode
        await HTTP.post(`docs/${document.id}/approve-correction`, { corrected: false });
      }
      this.docs[this.pageNumber].isValidated = !this.docs[this.pageNumber].isValidated;
    },
  },
  watch: {
    async selectedConversationId() {
      await this.submit();
    },
    docs() {
      Object.keys(this.docs).forEach((k) => {
        // If doc is validated, display humanTranscription, else humanTranscription
        // However, if doc is not validated, but humanTranscription exists, take that one
        const doc = this.docs[k];
        doc.text = (this.documentIsCorrected || (!this.documentIsCorrected && doc.humanTranscription !== '')
          ? doc.humanTranscription : doc.machineTranscription);
      });
    },
    annotations() {
      // fetch progress info.
      HTTP.get(`statistics?include=total&include=remaining&conversation=${this.selectedConversationId}`).then((response) => {
        this.total = response.data.total;
        this.remaining = response.data.remaining;
      });
    },
  },
  async created() {
    // Load conversations into drop down
    const response = await HTTP.get('conversations');
    this.conversations = response.data;
    // Select first item in the list if any
    if (this.conversations.length > 0) {
      this.selectedConversationId = this.conversations[0].id;
    }
  },
};
</script>
