Vue.use(VueResource);

var app = new Vue({
    el: '#status',
    data: {
        experiments: [],
        hash: null,
        detailed: null
    },
    methods: {
        getExperiments: function() {
            this.$http.get('/api/').then(function(response) {
                if (response.data.hash === this.hash) {
                    return;
                }

                this.hash = response.data.hash;
                this.experiments = response.data.experiments.sort(function(el) {
                    if (el.status.step === 'done') {
                        return el.experiment_id + Math.pow(10, 10);
                    } else {
                        return el.experiment_id;
                    }
                });
            });
        },
        remove: function(experiment, index) {
            this.$http.get('/api/delete/' + experiment.experiment_id).then(function(response) {
                this.experiments.splice(index, 1);
            });
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
