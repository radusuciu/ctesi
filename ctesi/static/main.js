Vue.use(VueResource);
Vue.use(VeeValidate);

var app = new Vue({
    el: '#app',
    data: {
        files: [],
        data: {
            name: '',
            type: '',
            organism: '',
            ip2username: '',
            ip2password: ''
        },
        progress: 0,
        uploadStatus: ''
    },
    methods: {
        onFileChange: function(e) {
            this.files = _.values(e.target.files);
        },

        onSubmit: function() {
            var onFinish = function(response, xhr) {
                if (xhr.status === 200) {
                    this.uploadStatus = 'success';
                } else {
                    this.uploadStatus = 'error';
                }
            }.bind(this);

            var onProgress = function(progress) {
                this.progress = progress;
            }.bind(this);

            this.uploadStatus = '';
            this._submitForm(this.data, this.files, onFinish, onProgress);
        },

        _submitForm: function(form, files, finishCallback, progressCallack) {
            this.$validator.validateAll();

            if (this.errors.any()) {
                return;
            }

            var url = '/';
            var formData = new FormData();
            var xhr = new XMLHttpRequest();

            formData.append('data', JSON.stringify(form));

            for (var i = 0, n = files.length; i < n; i++) {
                formData.append('files', files[i], files[i].name);
            }

            xhr.onreadystatechange = function(){
                if (xhr.readyState === 4) {
                    finishCallback(xhr.response, xhr);
                }
            };

            xhr.upload.onprogress = function(event) {
                var progress = Math.round(event.loaded / event.total * 100);
                progressCallack(progress);
            };

            xhr.open('POST', url, true);
            xhr.send(formData);
        }
    },
    filters: {
        toFixed: function(num) {
            return num.toFixed(1);
        }
    }
});


$(function() {
    $('.ui.checkbox').checkbox();
    $('.ui.dropdown').dropdown();
});