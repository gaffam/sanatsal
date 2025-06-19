const { createApp } = Vue;

createApp({
  data() {
    return {
      data: [],
      limit: 100,
      chart: null,
    };
  },
  methods: {
    async loadData() {
      try {
        const resp = await fetch(`/api/latest-data?limit=${this.limit}`);
        const arr = await resp.json();
        this.data = arr;
        this.drawChart();
      } catch (e) {
        console.error(e);
        alert('Failed to load data');
      }
    },
    drawChart() {
      const ctx = document.getElementById('chart').getContext('2d');
      const labels = this.data.map(d => d.date);
      const temps = this.data.map(d => d.temp);
      if (this.chart) this.chart.destroy();
      this.chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [{ label: 'Temperature', data: temps, borderColor: 'red', fill: false }]
        },
        options: {
          responsive: true,
          scales: { x: { display: true }, y: { display: true } }
        }
      });
    },
  },
  mounted() {
    this.loadData();
  }
}).mount('#app');
