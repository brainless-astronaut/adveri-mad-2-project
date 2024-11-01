<template>
  <div class="dashboard">
    <div class="counts">
      <v-row>
        <v-col cols="12" md="4">
          <v-card>
            <v-card-title>Sponsors Count</v-card-title>
            <v-card-text>{{ sponsors_count }}</v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" md="4">
          <v-card>
            <v-card-title>Influencers Count</v-card-title>
            <v-card-text>{{ influencers_count }}</v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" md="4">
          <v-card>
            <v-card-title>Campaigns Count</v-card-title>
            <v-card-text>{{ campaigns_count }}</v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" md="4">
          <v-card>
            <v-card-title>Flagged Sponsors</v-card-title>
            <v-card-text>{{ flagged_sponsors_count }}</v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" md="4">
          <v-card>
            <v-card-title>Flagged Influencers</v-card-title>
            <v-card-text>{{ flagged_influencers_count }}</v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" md="4">
          <v-card>
            <v-card-title>Flagged Campaigns</v-card-title>
            <v-card-text>{{ flagged_campaigns_count }}</v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </div>

    <!-- Industry Distribution Charts -->
    <div class="industry-charts">
      <h3>Industry Distribution</h3>
      <div class="chart-container">
        <canvas id="sponsorsChart"></canvas>
      </div>
      <div class="chart-container">
        <canvas id="influencersChart"></canvas>
      </div>
      <div class="chart-container">
        <canvas id="campaignsChart"></canvas>
      </div>
    </div>
  
    <!-- Flagged Entities Tables -->
    <div class="flagged-tables">
      <h3>Flagged Sponsors</h3>
      <v-simple-table>
        <thead>
          <tr>
            <th>Entity Name</th>
            <th>Industry</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="sponsor in flagged_sponsors" :key="sponsor.id">
            <td>{{ sponsor.entity_name }}</td>
            <td>{{ sponsor.industry }}</td>
          </tr>
        </tbody>
      </v-simple-table>

      <h3>Flagged Influencers</h3>
      <v-simple-table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Industry</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="influencer in flagged_influencers" :key="influencer.id">
            <td>{{ influencer.name }}</td>
            <td>{{ influencer.industry }}</td>
          </tr>
        </tbody>
      </v-simple-table>

      <h3>Flagged Campaigns</h3>
      <v-simple-table>
        <thead>
          <tr>
            <th>Campaign Name</th>
            <th>Sponsor</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="campaign in flagged_campaigns" :key="campaign.id">
            <td>{{ campaign.name }}</td>
            <td>{{ campaign.sponsor.entity_name }}</td>
          </tr>
        </tbody>
      </v-simple-table>
    </div>
  </div>
</template>
  
<script>
import { Chart } from 'chart.js';
import axios from 'axios';

export default {
  data() {
    return {
      sponsors_count: 0,
      influencers_count: 0,
      campaigns_count: 0,
      flagged_sponsors_count: 0,
      flagged_influencers_count: 0,
      flagged_campaigns_count: 0,
      flagged_sponsors: [],
      flagged_influencers: [],
      flagged_campaigns: [],
    };
  },
  methods: {
    fetchDashboardData() {
      axios.get('/admin/dashboard').then((response) => {
        const data = response.data;
        this.sponsors_count = data.sponsors_count;
        this.influencers_count = data.influencers_count;
        this.campaigns_count = data.campaigns_count;
        this.flagged_sponsors_count = data.flagged_sponsors_count;
        this.flagged_influencers_count = data.flagged_influencers_count;
        this.flagged_campaigns_count = data.flagged_campaigns_count;
        this.flagged_sponsors = data.flagged_sponsors;
        this.flagged_influencers = data.flagged_influencers;
        this.flagged_campaigns = data.flagged_campaigns;

        // Load charts
        this.loadChart('sponsorsChart', data.sponsors_by_industry);
        this.loadChart('influencersChart', data.influencers_by_industry);
        this.loadChart('campaignsChart', data.campaigns_by_industry);
      });
    },
    loadChart(chartId, data) {
      const ctx = document.getElementById(chartId).getContext('2d');
      new Chart(ctx, {
        type: 'bar',
        data: {
          labels: data.map((item) => item.industry),
          datasets: [
            {
              label: 'Count',
              data: data.map((item) => item.count),
              backgroundColor: 'rgba(75, 192, 192, 0.2)',
              borderColor: 'rgba(75, 192, 192, 1)',
              borderWidth: 1,
            },
          ],
        },
        options: {
          scales: {
            y: {
              beginAtZero: true,
            },
          },
        },
      });
    },
  },
  mounted() {
    this.fetchDashboardData();
  },
};
</script>
  
<style scoped>
.dashboard {
  padding: 20px;
}
.counts {
  margin-bottom: 30px;
}
.chart-container {
  width: 100%;
  height: 300px;
  margin-bottom: 30px;
}
.flagged-tables {
  margin-top: 30px;
}
.v-simple-table {
  margin-bottom: 30px;
}
</style>
  