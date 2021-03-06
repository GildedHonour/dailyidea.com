<template>
  <!-- Popup - Share Via Email -->
  <v-dialog
    v-model="visible"
    content-class="emailShareDialog"
    persistent
    max-width="400px"
  >
    <div class="closeBtn">
      <v-icon text class="cancelIcon" size="18" @click="closeDialog"
        >fas fa-times</v-icon
      >
    </div>

    <!-- Popup Header -->
    <div class="header">
      <v-icon text class="shareIcon" size="60">fas fa-envelope</v-icon>
      <div class="headlineText">Share Idea</div>
    </div>

    <form id="share-idea-without-login-form" @submit.stop.prevent="sendEmail">
      <v-text-field
        v-model="form.name"
        v-validate="'required|max:100'"
        :error-messages="errors.collect('name')"
        data-vv-name="name"
        label="Your Name"
        outlined
      >
      </v-text-field>
      <v-text-field
        v-model="form.friendName"
        v-validate="'required|max:100'"
        :error-messages="errors.collect('friend name')"
        data-vv-name="friend name"
        label=" Your Friend's Name"
        outlined
      ></v-text-field>
      <v-text-field
        v-model="form.friendEmail"
        v-validate="'required|email|max:100'"
        append-icon="email"
        :error-messages="errors.collect('email')"
        data-vv-name="email"
        label="Your Friend's Email "
        outlined
      ></v-text-field>

      <!-- Submit Buttons -->
      <div class="btnContainer">
        <v-btn class="cancelBtn" text @click="closeDialog">Cancel</v-btn>
        <v-btn
          type="submit"
          class="specialButton"
          :loading="sendingEmail"
          @click.stop.prevent="sendEmail"
          >Share</v-btn
        >
      </div>
      <div class="" style="text-align: center">
        <client-only>
          <a
            v-clipboard="() => getShareUrl()"
            href="#"
            @click.prevent.stop="onCopyShareLink"
            >Copy link to clipboard instead</a
          >
        </client-only>
      </div>
    </form>
  </v-dialog>
</template>

<script>
import shareIdea from '~/graphql/mutations/shareIdea'

export default {
  $_veeValidate: {
    validator: 'new'
  },
  props: {
    // Show loggedin or loggedout header
    visible: {
      type: Boolean,
      default: true
    },
    ideaId: {
      type: String,
      default: null
    },
    ideaOwnerId: {
      type: String,
      default: null
    }
  },
  data: () => ({
    valid: true,
    form: {
      name: '',
      friendName: '',
      friendEmail: ''
    },
    sendingEmail: false
  }),
  computed: {
    initialName() {
      return this.$store.getters['userData/userName']
    }
  },
  mounted() {
    this.form.name = this.initialName
  },
  methods: {
    cleanData() {
      this.sendingEmail = false
      this.form = {
        name: this.initialName,
        friendName: '',
        friendEmail: ''
      }
      this.errors.clear()
    },
    getShareUrl() {
      return document.location.href
    },
    async sendEmail() {
      const result = await this.$validator.validateAll()
      if (!result) {
        return
      }

      this.sendingEmail = true

      // Call shre idea over email api.
      try {
        await this.$amplifyApi.graphql({
          query: shareIdea,
          variables: {
            ideaId: this.ideaId,
            ideaOwnerId: this.ideaOwnerId,
            email: this.form.friendEmail,
            senderName: this.form.name,
            friendName: this.form.friendName
          },
          authMode: this.$store.state['userData/isAuthenticated']
            ? undefined
            : 'API_KEY'
        })
        this.$emit('success')
      } catch (e) {
        this.$emit('error')
      }
      this.close()
      this.cleanData()
    },
    close() {
      this.$validator.reset()
      this.$emit('close')
      this.cleanData()
    },
    closeDialog() {
      this.close()
    },
    onCopyShareLink() {
      this.$emit('onCopyShareLink')
      this.close()
    }
  }
}
</script>

<style lang="scss">
.emailShareDialog {
  padding: 15px 20px 20px 20px;
  background: white;

  .closeBtn {
    .cancelIcon {
      float: right;
    }
  }

  .header {
    text-align: center;
    margin-bottom: 20px;
    margin-top: 30px;

    .headlineText {
      margin: 20px 0px 20px 0px;
      font-size: 23px;
    }

    .cancelIcon {
      border: 1px solid red;
      float: right;
      padding-bottom: 10px;
    }
  }

  .shareIcon {
    color: rgba(255, 185, 45);
  }

  .btnContainer {
    /*margin-top: 20px;*/
    margin-bottom: 20px;
    text-align: right;
    .shareBtn {
      width: 170px;
    }
    .cancelBtn {
      background-color: #ebe7ed !important;
    }
  }
}
</style>
