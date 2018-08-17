/*jshint esversion: 6 */ 

Vue.use(VeeValidate);


var predefinedDiffMods = {
    'isotop': [{ comp: { c: 21, h: 36, o: 4, n: 8}, aa: 'C' , light: true }, { comp: { c: 16, h: 36, o: 4, n: 7, c13: 5, n15: 1}, aa: 'C' , heavy: true}],
    'Acetylation': { comp: { c: 2, h: 2, o: 1 }, aa: 'K' },
    'Deamidation': { comp: { 'n': -1, h: -1, o: 1 }, aa: 'NQ' },
    'Methyl ester': { comp: { c: 1, h: 2 }, aa: 'DE' },
    'Methionine Oxidation': { comp: { o: 1 }, aa: 'M'},
    'Oxidation on HW': { comp: { o: 1 }, aa: 'HW' },
    'Phosphorylation': { comp: { h: 1, o: 3, p: 1 }, aa: 'STY' },
    'Phosphorylation on HCDR': { comp: { h: 1, o: 3, p: 1 }, aa: 'HCDR' },
    'Beta-methylthiolation': { comp: { c: 1, h: 2, s: 1 }, aa: 'C'},
    'Biotin': { comp: { c: 10, h: 14, n: 2, o: 2, s: 1 }, aa: 'K' },
    'Carbamidomethyl': { comp: { c: 2, h: 3, n: 1, o: 1 }, aa: 'C' },
    'Carbamylation': { comp: { c: 1, h: 1, n: 1, o: 1}, aa: 'K' },
    'Carboxymethyl': { comp: { c: 2, h: 2, o: 2}, aa: 'C' },
    'Dehydration': { comp: { h: -2, o: -1 }, aa: 'DYTS' },
    'Dioxidation': { comp: { o: 2 }, aa: 'M' },
    'Formylation': { comp: { c: 1, o: 1}, aa: 'K' },
    'Carboxylation': { comp: { c: 1, o: 2 }, aa: 'E' },
    'Hexose': { comp: { c: 6, h: 10, o: 5}, aa: 'NSY' },
    'Guanidination': { comp: { c: 1, h: 2, n: 2}, aa: 'K' },
    'Hydroxylation': { comp: { o: 1 }, aa: 'PKDNRY' },
    'Myristoylation': { comp: { c: 14, h: 26, o: 1}, aa: 'KC' },
    'HexNAc': { comp: { c: 8, h: 15, o: 6, n: 1 }, aa: 'N' },
    'Propionamide': { comp: { c: 3, h: 5, n: 1, o: 1 }, aa: 'C' },
    'S-pyridylethyl': { comp: { c: 7, h: 7, n: 1 }, aa: 'C' },
    'Sulfation': { comp: { o: 3, s: 1 }, aa: 'YST' },
    'Sulphone': { comp: { o: 2 }, aa: 'M' },
    'Citrullination': { comp: { h: -1, n: -1, o: 1 }, aa: 'R' },
    'Dimethylation': { comp: { c: 2, h: 4 }, aa: 'KRN' },
    'Farnesylation': { comp: { c: 15, h: 24 }, aa: 'C' },
    'Geranylation': { comp: { c: 20, h: 32 }, aa: 'C' },
    'Lipoyl': { comp: { c: 8, h: 12, o: 1, s: 2 }, aa: 'K' },
    'Methylation': { comp: { c: 1, h: 2 }, aa: 'TSCKRHDE' },
    'Palmitoylation': { comp: { c: 16, h: 30, o: 1 }, aa: 'CSTK' },
    'Trimethylation': { comp: { c: 3, h: 6 }, aa: 'KR' },
    'Ubiquitin': { comp: { c: 4, h: 6, n: 2, o: 2 }, aa: 'TSCK' },
    'FAD': { comp: { c: 27, h: 31, n: 9, o: 15}, aa: 'CHY' },
    'HNE': { comp: { c: 9, h: 16, o: 2 }, aa: 'CHK' },
    'Tripalmitate': { comp: { c: 51, h: 96, o: 5}, aa: 'C' },
    'SMA': { comp: { c: 6, h: 9, o: 2, n: 1 }, aa: 'K' },
    'Phosphopantetheine': { comp: { c: 11, h: 21, n: 2, o: 6, p: 1, s: 1}, aa: 'S' },
    'PyridoxalPhosphate': { comp: { c: 8, h: 8, n: 1, o: 5, p: 1}, aa: 'K' }
};

function calculateDiffModMass(comp) {
    var massMap = {
        c: 12,
        h: 1.007825,
        o: 15.994915,
        n: 14.003074,
        s: 31.972072,
        p: 30.973763,
        h2: 2.014102,
        c13: 13.003355,
        n15: 15.000109,
        hplus: 1.0072765
    };

    var mass = 0;

    for (var el in comp) {
        mass += massMap[el] * comp[el];
    }

    return mass.toFixed(6);
}


Vue.component('diff-mod-picker', {
    template: `
        <div class="ui right floated bottom pointing dropdown primary button">
            <span>Add Diff Mod</span>
            <div class="menu">
                <div class="ui icon search input">
                    <i class="search icon"></i>
                    <input type="text" placeholder="Search diff mods">
                </div>
                <div class="scrolling menu">
                    <div v-for="(value, key) in predefinedDiffMods" class="item">
                        {{ key }}
                    </div>
                </div>
                <div class="item" data-value="">
                    <button type="button" class="fluid ui button">Blank Diff Mod</button>
                </div>
            </div>
        </div>
    `,
    data: function() {
        return {
            predefinedDiffMods: predefinedDiffMods
        }
    },
    methods: {
        pick: function(value, text) {
            this.$emit('pick', this.predefinedDiffMods[text]);
        }
    },
    mounted: function() {
        $(this.$el).dropdown({
            onChange: this.pick
        });
    }
});

Vue.component('diff-mod', {
    template: `
        <tr class="center aligned diff-mod">
            <td><div class="ui input"><input class="aa" v-model="aa" type="text"></div></td>
            <td><div class="ui small input"><input v-model="comp.c" type="number"></div></td>
            <td><div class="ui small input"><input v-model="comp.h" type="number"></div></td>
            <td><div class="ui small input"><input v-model="comp.o" type="number"></div></td>
            <td><div class="ui small input"><input v-model="comp.n" type="number"></div></td>
            <td><div class="ui small input"><input v-model="comp.s" type="number"></div></td>
            <td><div class="ui small input"><input v-model="comp.p" type="number"></div></td>
            <td><div class="ui small input"><input v-model="comp.c13" type="number"></div></td>
            <td><div class="ui small input"><input v-model="comp.h2" type="number"></div></td>
            <td><div class="ui small input"><input v-model="comp.n15" type="number"></div></td>
            <td><div class="ui fitted checkbox"><input type="checkbox" v-model="light"></div></td>
            <td><div class="ui fitted checkbox"><input type="checkbox" v-model="heavy"></div></td>
            <td>{{ mass }}<input type="hidden" :value="state"></td>
            <td><i @click="remove()" class="icon close"></i></td>
        </tr>
    `,
    props: ['initComp', 'initAa', 'index', 'initLight', 'initHeavy'],
    data: function() {
        var defaultComp = { c: 0, h: 0, o: 0, n: 0, p: 0, s: 0, c13: 0, h2: 0, n15: 0 };
        var defaultLight, defaultHeavy;

        // assume we want the diff mod to apply to both heavy and light if nothing is passed
        if (this.initLight === undefined && this.initHeavy === undefined) {
            defaultLight = defaultHeavy = true
        }

        return {
            light: this.initLight || defaultLight,
            heavy: this.initHeavy || defaultHeavy,
            aa: this.initAa || '',
            comp: Vue.util.extend(defaultComp, this.initComp),
        };
    },
    methods: {
        remove: function() {
            this.$emit('remove');
        }
    },
    computed: {
        mass: function() {
            var massMap = {
                c: 12,
                h: 1.007825,
                o: 15.994915,
                n: 14.003074,
                s: 31.972072,
                p: 30.973763,
                h2: 2.014102,
                c13: 13.003355,
                n15: 15.000109,
                hplus: 1.0072765
            };

            var mass = 0;

            for (var el in this.comp) {
                mass += massMap[el] * this.comp[el];
            }

            return mass.toFixed(6);
        },
        state: function() {
            var state = {
                aa: this.aa.toUpperCase(),
                comp: this.comp,
                mass: this.mass,
                index: this.index,
                light: this.light,
                heavy: this.heavy
            }

            this.$emit('state', state);

            return state;
        }
    },
    mounted: function() {
        $('.ui.checkbox').checkbox();
    }
});

var app = new Vue({
    el: '#app',
    data: {
        files: [],
        experimentId: null,
        data: {
            name: '',
            type: '',
            organism: '',
            ip2username: '',
            ip2password: '',
            remember_ip2: true,
            email: true,
            options: {},
        },
        diffMods: [],
        progress: 0,
        disabled: false,
        uploadStatus: '',
        advanced: false,
        askForIP2: true,
        defaultOptions: {
            minPeptidesPerProtein: 1,
            maxNumDiffmod: 1
        }
    },
    watch: {
        'data.type': function(newType) {
            // if experiment type changes we check if the type needs certain diff mods
            // note that we do this even if the advanced pane is hidden
            this.removeAllDiffMods();

            if (predefinedDiffMods.hasOwnProperty(this.data.type)) {
                var diffMods = predefinedDiffMods[this.data.type];

                for (var i = 0, n = diffMods.length; i < n; i++) {
                    diffMods[i].mass = calculateDiffModMass(diffMods[i].comp)
                    this.addDiffMod(diffMods[i]);
                }
            }
        }
    },
    methods: {
        onFileChange: function(e) {
            this.files = _.map(_.values(e.target.files), function(file) {
                return {
                    file: file,
                    progress: 0,
                    status: ''
                }
            });
        },

        addDiffMod: function(mod) {
            mod = mod || {};

            if (!_.isArray(mod)) {
                mod = [ mod ]
            }

            for (var i = 0, n = mod.length; i < n; i++) {
                mod[i].index = _.uniqueId();
                this.diffMods.push(mod[i]);
            }
        },

        removeDiffMod: function(index) {
            this.diffMods.splice(index, 1);
        },

        removeAllDiffMods: function() {
            this.diffMods = [];
        },

        updateState: function(updated) {
            var mod = _.find(this.diffMods, function(el) {
                return el.index == updated.index;
            });

            if (mod) {
                mod = Vue.util.extend(mod, updated);
            }
        },

        showAdvanced: function() {
            // only including these options in the data sent to server if
            // they are actually visible on the user's screen
            this.data.options = this.defaultOptions;
            this.advanced = true;
        },

        onSubmit:function() {
            this.$validator.validateAll();

            this.verifyIP2(this._onSubmit, function(response) {
                this.askForIP2 = true;
                this.errors.add('ip2_password', 'Could not login to IP2 with provided credentials.', 'auth');
            }.bind(this));
        },

        verifyIP2: function(onSuccess, onError) {
            var payload = {};

            if (this.askForIP2) {
                payload = {
                    username: this.data.ip2username,
                    password: this.data.ip2password
                }
            }

            axios.post('/api/ip2_auth', payload).then(function(response) {
                if (response.data) {
                    onSuccess(response);
                } else {
                    onError(response);
                }
            }.bind(this), onError);
        },

        leaving: function(e) {
            if (!this.uploadStatus && this.progress) {
                var message = 'Your files are not finished uploading just yet. Are you sure you want to leave?';
                e.returnValue = message;
                return message;
            } else {
                return;
            }
        },

        _isValid: function() {
            this.$validator.validateAll();
            return !this.errors.any();
        },

        _onSubmit: function() {
            if (!this._isValid() || this.disabled) {
                return;
            }

            this.uploadStatus = '';
            this.experimentId = null;

            // disable form once we start submit process
            this.disabled = true;

            // this.data stores data that will be sent to server
            this.data.diffMods = this.diffMods;

            var onSuccess = function() {
                this.uploadStatus = 'success';
            }.bind(this);

            var onError = function() {
                this.uploadStatus = 'error';
            }.bind(this);

            // first make request to add new experiment
            // note that this will set an experimentId which is needed to submit files
            this._submitData()
                // if we've successfully made a new experiment then we submit files
                .then(this._submitFiles)
                // and then make another request to tell the server to start processing
                .then(this._startProcessing)
                .then(onSuccess)
                .catch(onError)
                .then(function() {
                    // enable form for re-submission regardless of outcome
                    this.disabled = false;
                }.bind(this));
        },

        _startProcessing: function() {
            return axios.get('/api/process/' + this.experimentId);
        },

        _submitData: function() {
            var request = axios.post('/api/experiment', this.data).then(function(response) {
                this.experimentId = response.data.experiment_id;
            }.bind(this));

            return request;
        },

        _submitFiles: function() {
            var url = '/api/upload/' + this.experimentId;

            var progress = function(file, progressEvent) {
                var progress = Math.round(progressEvent.loaded / progressEvent.total * 100);
                file.progress = progress;

                var totalProgress = 0;
                // keeping track of overall progress
                for (var i = 0, n = this.files.length; i < n; i++) {
                    totalProgress += this.files[i].progress;
                }

                this.progress = totalProgress / this.files.length;
            };

            var requests = [];

            for (var i = 0, n = this.files.length; i < n; i++) {
                var formData = new FormData();
                var f = this.files[i];
                formData.append('files', f.file, f.file.name);

                f.progress = 0;
                f.status = '';

                requests.push(axios.post(url, formData, {
                    onUploadProgress: progress.bind(this, f)
                }).then(function(response) {
                    // note that `this` is bound to f
                    // if this is not done, then all the callbacks
                    // will refer to the last f in the loop
                    this.status = 'success';
                }.bind(f)).catch(function(errors) {
                    this.status = 'error';
                    // rejecting promise to be handled be caught after all of these
                    // are wrapped by axios.all
                    return Promise.reject();
                }.bind(f)));
            }

            return axios.all(requests);
        },
    },
    filters: {
        toFixed: function(num) {
            return num.toFixed(1);
        }
    },
    mounted: function() {
        $('.ui.checkbox').checkbox();
        $('.field .ui.dropdown').dropdown();

        window.addEventListener('beforeunload', this.leaving);

        if (window.hasOwnProperty('bootstrap') && window.bootstrap.hasOwnProperty('ip2_authd')) {
            this.askForIP2 = !window.bootstrap.ip2_authd;
        }
    }
});
