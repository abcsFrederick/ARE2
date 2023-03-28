import axios from '@/utils/http';
// import $ from 'jquery';
const base = {    
    sq: 'http://localhost:8000',
    // sq: 'https://fsivgl-img01p.ncifcrf.gov/api/v1',
    bd: 'http://xxxxx22222.com/api'
}

const api = {
    submit(file, username, password) {
        var formData = new FormData();
        formData.append('file', file);
        formData.append('username', username);
        formData.append('password', password);
        // $.ajax({
        //     url: `${base.sq}/workflow1/submit`,
        //     data: formData,
        //     type: "POST",
        //     processData: false,
        //     contentType: false
        // });
        console.log(`${base.sq}/workflow1/submit`)
        return axios.post(`${base.sq}/workflow1/submit`, formData, {
            headers: {
              "Content-Type": "multipart/form-data",
            }
        })
    },
    record(id) {
        return axios.get(`${base.sq}/workflow1/celery_task`, { params: { taskId: id } })
    },
    images(id) {
        return axios.get(`${base.sq}/workflow1/task_images`, { params: { taskId: id } })
    },
    layerAndROIs(imageIndex) {
        return axios.get(`${base.sq}/workflow1/image_layers_rois`, { params: { imageIndex: imageIndex } })
    }
}
export default api;