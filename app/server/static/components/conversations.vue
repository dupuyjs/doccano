<template lang="pug">
extends ./conversations.pug

block conversations-selection
  div
    | Please select a conversation:
    div.control
      select(v-model="selectedConversationId", name="selectedConversationId", required)
        option(v-for="c in conversations", v-bind:value="c.id") {{ parseConversationsTitle(c) }}

block annotation-area
  div.card(
      v-if="docs[pageNumber] && annotations[pageNumber] && documentIsCorrected"
    )
      header.card-header
        div.card-header-title.has-background-royalblue
          div.field.is-grouped.is-grouped-multiline
            div.control(v-for="label in labels")
              div.tags.has-addons
                a.tag.is-medium(
                  v-shortkey.once="replaceNull(shortcutKey(label))"
                  v-bind:style="{ \
                    color: label.text_color, \
                    backgroundColor: label.background_color \
                  }"
                  v-on:click="annotate(label.id)"
                  v-on:shortkey="annotate(label.id)"
                ) {{ label.text }}
                span.tag.is-medium
                  kbd {{ shortcutKey(label) | simpleShortcut }}

      div.card-content
        div.content.scrollable(ref="textbox")
          annotator(
            v-bind:labels="labels"
            v-bind:entity-positions="annotations[pageNumber]"
            v-bind:search-query="searchQuery"
            v-bind:text="docs[pageNumber].text"
            v-on:remove-label="removeLabel"
            v-on:add-label="addLabel"
            ref="annotator"
          )
  
  corrector(
    v-if="docs[pageNumber] && annotations[pageNumber] && !documentIsCorrected"
    v-bind:text="docs[pageNumber].text"
    v-bind:audioFile="this.conversations.find(c => c.id === this.selectedConversationId).audioFile"
    v-on:dataChanged="getCorrectedText"
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
import Annotator from './annotator.vue';
import Corrector from './corrector.vue';

import HTTP from './http';
import { simpleShortcut } from './filter';

export default {

  data() {
    return {
      conversations: [],
      selectedConversationId: 0,
      correctedText: ""
    };
  },

  filters: { simpleShortcut },

  components: { Annotator, Corrector },

  mixins: [annotationMixin],

  computed: {
    
    documentIsCorrected() {
      const document = this.docs[this.pageNumber];
      return document != null && document.textValidated;
    },

    approveDocumentCorrectionTooltip() {
      return this.documentIsCorrected
        ? `Correction done, click to correct transcript`
        : 'Click to correct transcript';
    },

  },

  methods: {
    
    annotate(labelId) {
      this.$refs.annotator.addLabel(labelId);
    },

    addLabel(annotation) {
      const docId = this.docs[this.pageNumber].id;
      HTTP.post(`docs/${docId}/annotations`, annotation).then((response) => {
        this.annotations[this.pageNumber].push(response.data);
      });
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
      var c = JSON.parse(conversation.metadata);
      if (c.service !== undefined)
        return c.service;
      else return `Conversation ${c.id}`;
    },

    getCorrectedText(text) {
      this.correctedText = text;
    },

    async approveDocumentCorrection() {
      const document = this.docs[this.pageNumber];
      if (!this.documentIsCorrected)
      {
        // Edit mode
        const correctedText = this.$refs.corrector.getText();
        const corrected = true;
        var response = await HTTP.post(`docs/${document.id}/approve-correction`, { corrected, correctedText });
        document.text = correctedText;
      }
      else {
        // Not-edit mode
        const corrected = false;
        var response = await HTTP.post(`docs/${document.id}/approve-correction`, { corrected });
      }
      this.docs[this.pageNumber].textValidated = !this.docs[this.pageNumber].textValidated
    },

  },

  watch: {
    selectedConversationId: async function () {
      await this.submit();
    },

    docs: function() {
      Object.keys(this.docs).forEach(k => {
        // If doc is validated, display humanTranscription, else humanTranscription
        // However, if doc is not validated, but humanTranscription exists, take that one
        let doc = this.docs[k];
        doc.text = (this.documentIsCorrected || (!this.documentIsCorrected && doc.humanTranscription != "") ? 
          doc.humanTranscription : doc.machineTranscription);
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
    var response = await HTTP.get('conversations')
    this.conversations = response.data;
    // Select first item in the list if any
    if (this.conversations.length > 0) {
      this.selectedConversationId = this.conversations[0].id;
    }

  }
};
</script>
