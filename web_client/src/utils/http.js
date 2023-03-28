import axios from 'axios';
import { Toast } from 'vant';
// import Vue from 'vue';

// Vue.use(Toast);


const tip = msg => {
	console.log(msg)
	Toast({
		message: msg,
		duration: 1000,
		forbidClick: true
	})
}

const errorHandle = (status, other) => {
	switch(status) {
		case 404:
			tip('resource not exist');
			break;
		default:
			tip(`Error code ${other}`);
	}
}

var instance = axios.create({ timeout: 1000 * 15 });
// instance.defaults.headers.post['Content-type'] = 'application/x-www-form-urlencoded';

instance.interceptors.response.use(
	res => res.status === 200 ? Promise.resolve(res): Promise.reject(res),
	error => {
		const {response} = error;
		if (response) {
			errorHandle(response.status, response.data.message);
			return Promise.reject(response);
		} else {
			if (!window.navigator.onLine) {
               // store.commit('changeNetwork', false);
            } else {
                return Promise.reject(error);
            }
		}
	});

export default instance;
