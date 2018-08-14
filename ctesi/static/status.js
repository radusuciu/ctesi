var app = new Vue({
    el: '#status',
    data: {
        experiments: [],
        hash: null,
        detailed: null
    },
    methods: {
        getExperiments: function() {
            if (document.hidden) {
                return;
            }

            axios.get('/api/').then(function(response) {
                if (response.data.hash === this.hash) {
                    return;
                }

                this.hash = response.data.hash;

                this.experiments = _.sortBy(response.data.experiments, [function(el) {
                    if (el.status.state === 'done') {
                        return el.experiment_id + Math.pow(10, 10);
                    } else {
                        return el.experiment_id;
                    }
                }]);
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
