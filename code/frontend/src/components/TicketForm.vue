<template>
  <div
    class="ticket-form"
    style="margin-top: 5px; margin-left: 5px; margin-right: 5px; text-align: left"
  >
    <b-form @submit="onSubmit" @reset="onReset" v-if="show">
      <b-form-group>
        <b-form-input
          id="input-title"
          v-model="form.title"
          type="text"
          placeholder="Enter title"
          :state="check_title"
          aria-describedby="input-live-feedback-title"
          :disabled="user_role == 'student' ? false : true"
          required
        ></b-form-input>
        <b-form-invalid-feedback id="input-live-feedback-title">
          Title should be at least 5 characters long.
        </b-form-invalid-feedback>
      </b-form-group>

      <b-form-group>
        <b-form-textarea
          id="input-description"
          v-model="form.description"
          type="text"
          placeholder="Enter description"
          rows="3"
          max-rows="6"
          :state="check_description"
          :disabled="user_role == 'student' ? false : true"
          required
        ></b-form-textarea>
        <b-form-invalid-feedback id="input-live-feedback-description">
          Description should be at least 5 characters long.
        </b-form-invalid-feedback>
      </b-form-group>

      <Tagging
        @tags_changed="onTagsChanged"
        v-show="user_role == 'student' ? true : false"
      ></Tagging>

      <b-form-group v-if="user_role == 'student'">
        <b-form-radio-group
          id="radio-group-priority"
          v-model="form.priority"
          :options="priority_options"
          name="radio-group-priority"
        ></b-form-radio-group>
        <b-form-select v-if="form.priority === 'high'" v-model="selectedOption">
          <option value="">Select an option</option>
          <option value="Portal Down">Portal Down</option>
          <option value="Doubt in Quiz">Doubt in Quiz or End Term</option>
          <option value="Fees related isuue">Fees Related Issue</option>
        </b-form-select>
      </b-form-group>

      <b-form-group v-if="user_role !== 'student'">
        <b-form-textarea
          id="input-solution"
          v-model="form.solution"
          type="text"
          placeholder="Enter solution"
          rows="3"
          max-rows="6"
        ></b-form-textarea>
      </b-form-group>

      <FileUpload @file_uploading="onFileUpload"></FileUpload>

      <br />
      <br />
      <b-button style="margin: 10px" type="submit" variant="primary">Submit</b-button>
      <b-button v-show="hideReset ? false : true" style="margin: 10px" type="reset" variant="danger"
        >Reset</b-button
      >
    </b-form>
    <br />
  </div>
</template>

<script>
import * as common from "../assets/common.js";
import FileUpload from "./FileUpload.vue";
import Tagging from "./Tagging.vue";

export default {
  name: "TicketForm",
  props: ["ticket_id", "title", "description", "priority", "tags", "hideReset", "editTicket"],
  components: { Tagging, FileUpload },
  data() {
    return {
      priority_options: [
        { text: "Low", value: "low" },
        { text: "Medium", value: "medium" },
        { text: "High", value: "high" },
      ],
      form: {
        title: this.title ? this.title : "",
        description: this.description ? this.description : "",
        priority: this.priority ? this.priority : "low",
        solution: "",
        tags: [],
        tag_1: "",
        tag_2: "",
        tag_3: "",
        attachments: [],
      },
      user_role: this.$store.getters.get_user_role,
      show: true,
      selectedOption: "",
    };
  },
  created() {},
  methods: {
    onFileUpload(value) {
      this.form.attachments.splice(0, this.form.attachments.length, ...value);
    },
    onSubmit(event) {
    if (event && event.preventDefault) {
      event.preventDefault();
    }

    if (this.user_role == "student" && this.form.tags.length == 0 && !this.check_title() && !this.check_description()) {
      alert("Choose at least 1 tag and title and description should be at least 5 characters long.");
    } else {
      alert('Submitting form. Click "Ok" to proceed?');
      this.$log.info("Submitting Ticket form");

      for (let i in this.form.tags) {
        if (this.form.tags[i]) {
          this.form[`tag_${parseInt(i) + 1}`] = this.form.tags[i];
        }
      }

      let fetch_url = "";
      let method = "";
      if (this.editTicket) {
        fetch_url = common.TICKET_API + `/${this.ticket_id}` + `/${this.$store.getters.get_user_id}`;
        method = "PUT";
      } else {
        fetch_url = common.TICKET_API + `/${this.$store.getters.get_user_id}`;
        method = "POST";
      }

      // Send request to existing URL
      fetch(fetch_url, {
        method: method,
        headers: {
          "Content-Type": "application/json",
          web_token: this.$store.getters.get_web_token,
          user_id: this.$store.getters.get_user_id,
        },
        body: JSON.stringify(this.form),
      })
      .then((response) => response.json())
      .then((data) => {
        // Handle response from existing URL if needed
      })
      .catch((error) => {
        this.$log.error(`Error : ${error}`);
        this.flashMessage.error({
          message: "Internal Server Error",
        });
      });

      // Send request to webhook API if priority is high
      if (this.form.priority === 'high' && this.selectedOption) {
          const lowerCaseDescription = this.form.description.toLowerCase();
      const lowerCaseOption = this.selectedOption.toLowerCase();

      if (!lowerCaseDescription.includes(lowerCaseOption)) {
        alert("The selected option must be mentioned in the description for high priority.");
        return;
      }

        const payload = {
        sender: this.$store.getters.get_user_name,
        post: this.form.description,

        };
        console.log("check1:", payload);
        fetch('http://127.0.0.1:5000/api/v1/webhook',  {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),

        })
        .then((response) => {
          if (!response.ok) {
            throw new Error('Failed to send webhook request');
          }
          return response.json();
        })
        .then((data) => {
          // Handle response from webhook API if needed
        })
        .catch((error) => {
          this.$log.error(`Error sending webhook request: ${error}`);
          // Handle error from webhook API if needed
        });
      }
    }
  },
    onReset(event) {
      if (event && event.preventDefault) {
        event.preventDefault();
      }
      this.form.title = "";
      this.form.description = "";
      this.solution = "";
      this.form.attachments = [];
      this.form.tags = [];
      this.show = false;
      this.$nextTick(() => {
        this.show = true;
      });
    },
    onTagsChanged(value) {
      this.form.tags = value;
    },
  },
  computed: {
    check_title() {
      return this.form.title.length > 15;
    },
    check_description() {
      return this.form.description.length >= 5 ? true : false;
    },
  },
};
</script>

<style></style>
