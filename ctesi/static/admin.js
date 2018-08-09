var app = new Vue({
    el: '#status',
    data: {
        experiments: []
    },
    methods: {
        getExperiments: function() {
            if (document.hidden) {
                return;
            }

            axios.get('/api/admin').then(function(response) {
                this.experiments = response.data.experiments;
            }.bind(this));
        },
        remove: function(experiment, index) {
            axios.get('/api/delete/' + experiment.experiment_id).then(function(response) {
                this.experiments.splice(index, 1);
            }.bind(this));
        }
    },
    filters: {
        prettyDate: function(dateString) {
            var date = new Date(dateString);
            return date.toLocaleDateString(
                'en-US',
                { year: 'numeric', month: 'long', day: 'numeric', hour: 'numeric', minute: 'numeric' }
            );
        }
    },
    beforeMount: function() {
        this.getExperiments();
        setInterval(this.getExperiments.bind(this), 5000);
    }
});
