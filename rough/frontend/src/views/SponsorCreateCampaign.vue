<template>
    <div class="create-campaign">
      <h1>Create a New Campaign</h1>
      <form @submit.prevent="createCampaign">
        <div class="form-group">
          <label for="name">Campaign Name:</label>
          <input v-model="campaign.name" type="text" id="name" placeholder="Enter campaign name" required />
        </div>
  
        <div class="form-group">
          <label for="description">Description:</label>
          <textarea v-model="campaign.description" id="description" placeholder="Enter campaign description" required></textarea>
        </div>
  
        <div class="form-group">
          <label for="start_date">Start Date:</label>
          <input v-model="campaign.start_date" type="date" id="start_date" required />
        </div>
  
        <div class="form-group">
          <label for="end_date">End Date:</label>
          <input v-model="campaign.end_date" type="date" id="end_date" required />
        </div>
  
        <div class="form-group">
          <label for="budget">Budget:</label>
          <input v-model="campaign.budget" type="number" id="budget" placeholder="Enter campaign budget" required />
        </div>
  
        <div class="form-group">
          <label for="goals">Goals:</label>
          <input v-model="campaign.goals" type="text" id="goals" placeholder="Enter campaign goals" required />
        </div>
  
        <div class="form-group">
          <label for="visibility">Visibility:</label>
          <select v-model="campaign.visibility" id="visibility">
            <option value="public">Public</option>
            <option value="private">Private</option>
          </select>
        </div>
  
        <button type="submit">Create Campaign</button>
      </form>
  
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      <p v-if="successMessage" class="success">{{ successMessage }}</p>
    </div>
  </template>
  
  <script>
  import axios from 'axios';
  
  export default {
    data() {
      return {
        campaign: {
          name: '',
          description: '',
          start_date: '',
          end_date: '',
          budget: '',
          goals: '',
          visibility: 'public',
        },
        errorMessage: '',
        successMessage: ''
      };
    },
    methods: {
      async createCampaign() {
        try {
          // Reset messages
          this.errorMessage = '';
          this.successMessage = '';
  
          // Send POST request to create a campaign
          const response = await axios.post('/sponsor/create_campaign', this.campaign, {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('token')}`,  // Assuming JWT is stored in localStorage
            }
          });
  
          // Handle success
          if (response.status === 201) {
            this.successMessage = 'Campaign created successfully!';
            this.clearForm();  // Reset form after successful submission
          }
        } catch (error) {
          // Handle error response
          if (error.response && error.response.data.error) {
            this.errorMessage = error.response.data.error;
          } else {
            this.errorMessage = 'An error occurred. Please try again.';
          }
        }
      },
      clearForm() {
        this.campaign = {
          name: '',
          description: '',
          start_date: '',
          end_date: '',
          budget: '',
          goals: '',
          visibility: 'public',
        };
      }
    }
  };
  </script>
  
  <style scoped>
  .create-campaign {
    max-width: 500px;
    margin: 0 auto;
  }
  
  .form-group {
    margin-bottom: 1em;
  }
  
  label {
    display: block;
    margin-bottom: 0.5em;
  }
  
  input, textarea, select {
    width: 100%;
    padding: 0.5em;
    margin-bottom: 0.5em;
    border: 1px solid #ccc;
    border-radius: 4px;
  }
  
  button {
    background-color: #28a745;
    color: white;
    border: none;
    padding: 0.7em;
    border-radius: 4px;
    cursor: pointer;
  }
  
  button:hover {
    background-color: #218838;
  }
  
  .error {
    color: red;
    font-weight: bold;
  }
  
  .success {
    color: green;
    font-weight: bold;
  }
  </style>
  