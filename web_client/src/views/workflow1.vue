<template>
  <v-app>
    <div
      id="blueimp-gallery"
      class="blueimp-gallery blueimp-gallery-controls"
      aria-label="image gallery"
      aria-modal="true"
      role="dialog"
    >
      <div class="slides" aria-live="polite"></div>
      <h3 class="title"></h3>
      <a
        class="prev"
        aria-controls="blueimp-gallery"
        aria-label="previous slide"
        aria-keyshortcuts="ArrowLeft"
      ></a>
      <a
        class="next"
        aria-controls="blueimp-gallery"
        aria-label="next slide"
        aria-keyshortcuts="ArrowRight"
      ></a>
      <a
        class="close"
        aria-controls="blueimp-gallery"
        aria-label="close"
        aria-keyshortcuts="Escape"
      ></a>
      <a
        class="play-pause"
        aria-controls="blueimp-gallery"
        aria-label="play slideshow"
        aria-keyshortcuts="Space"
        aria-pressed="false"
        role="button"
      ></a>
      <ol class="indicator"></ol>
    </div>
    <v-app-bar
      color="#008cba"
      dense
      dark
      app
    >
      <v-container
        grid-list-xl
      >
        <v-toolbar-title>Aperio Image ROI Extraction Workflow
          <v-btn 
            icon
            href="mailto:miaot2@nih.gov?Subject=Aperio%20Workflow"
          >
            <v-icon>mdi-email</v-icon>
          </v-btn>
        </v-toolbar-title>
      </v-container>
    </v-app-bar>
    <v-main>
      <v-container
        grid-list-xl
      >
        <v-layout row wrap>
          <v-flex xs12 class="page-header">
            <h3>ROI Extraction Report</h3>
          </v-flex>
          <v-flex v-if="processing" xs12>
            <!--<p style="white-space: pre;">{{reports}}</p>-->
            <div v-for="report in reports" :key="report">
              {{ report }}
            </div>
          </v-flex>
          <v-flex v-else xs12>
            <p>Processing complete. Click tabs to navigate between sets. Click on thumbnails to enlarge images.</p>
            <v-simple-table>
              <template v-slot:default>
                <thead>
                  <tr>
                    <th class="text-center">
                      Total Number & Time Taken
                    </th>
                    <th class="text-center">
                      Download Complete Extraction
                    </th>
                    <th class="text-center">
                        Reference ID
                    </th>
                    <th class="text-center">
                      Line Annotations
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td class="text-center">{{ numberOfRoIs }} ROIs extracted in {{ processTime }}</td>
                    <td class="text-center">
                      <v-btn 
                        color="primary"
                      >
                        <a class="download" :href=link>Download ROIs({{size}})</a>
                      </v-btn>
                    </td>
                    <td class="text-center">{{referenceId}}</td>
                    <td class="text-center">
                      <v-btn v-if="lineFileLink"
                        color="primary"
                      >
                        <a class="download" :href=lineFileLink>Download Line Annotations</a>
                      </v-btn>
                    </td>
                  </tr>
                </tbody>
              </template>
            </v-simple-table>
            <row>
              <v-tabs
                center-active
                show-arrows
              >
                <v-tab :id="img.index" :value="img.image" v-for="img in images" :key="img" @click="changeImageId">
                    {{ img.image }}
                </v-tab>
              </v-tabs>
              <v-simple-table v-for="selectedROI, name in selectedImageROI" :key="selectedROI">
                <template v-slot:default>
                  <thead>
                    <tr>
                      <th class="text-left">
                        Image ID
                      </th>
                      <th class="text-left">
                        Annotation Layer
                      </th>
                      <th class="text-left">
                        Extracted ROIs of Current Set
                      </th>
                      <th class="text-left">
                        Options
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td class="text-left">{{selectedImage}}</td>
                      <td class="text-left">{{name}}</td>
                      <td class="text-left">{{selectedROI.numOfRois}}</td>
                      <td class="text-left">Download this set</td>
                    </tr>
                    <tr colspan='6'>
                      <td colspan='6'>
                        <div id='links'>
                          <a :href=selectedImgRoi v-for="selectedImgRoi in selectedROI.rois" :key="selectedImgRoi" @click='show'>
                            <img :src=selectedImgRoi>
                          </a>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </template>
              </v-simple-table>
            </row>
          </v-flex>
        </v-layout>
      </v-container>
      <v-footer padless>
        <v-container>
          <v-col
            class="text-left"
            cols="12"
          >
            © Imaging and Visualization Group, ABCS - {{year}}
          </v-col>
          
        </v-container>
        </v-footer>
    </v-main>
</v-app>
</template>


<script>
import "blueimp-gallery/css/blueimp-gallery.min.css";
import Gallery from "blueimp-gallery/js/blueimp-gallery.min.js";
import { sanitizeUrl } from '@braintree/sanitize-url'

const ws = process.env.VUE_APP_WEBSOCKET_URL;

export default {
  name: 'home',
  props: ['id'],
  data: () => ({
    reports: [],
    link: '220928_9968094252/Pen-Tool-Test-20220719-SpectrumData_ROIs_2022_09_28_03-01_PM.zip',
    lineFileLink: null,
    size: '100MB',
    numberOfRoIs: 300,
    processTime: '10s',
    referenceId: '',
    images: [{
        "image": "17009872",
        "index": 32
    }],
    selectedImage: '4123',
    selectedImageIndex: '1',
    selectedImageROI: {
      // "None": {
      //   "numOfRois": 15,
      //   "rois": ['ARE2/workspace/221001_1255845671/output_p/17009872/0321072E--01-16-14_1_0321072E--01-16-14_17009872_01.jpg',
      //   'ARE2/workspace/221001_1255845671/output_p/17009872/0321072E--01-16-14_1_0321072E--01-16-14_17009872_02.jpg',
      //   'ARE2/workspace/221001_1255845671/output_p/17009872/0321072E--01-16-14_1_0321072E--01-16-14_17009872_03.jpg',
      //   'ARE2/workspace/221001_1255845671/output_p/17009872/0321072E--01-16-14_1_0321072E--01-16-14_17009872_04.jpg',
      //   'ARE2/workspace/221001_1255845671/output_p/17009872/0321072E--01-16-14_1_0321072E--01-16-14_17009872_05.jpg',
      //   'ARE2/workspace/221001_1255845671/output_p/17009872/0321072E--01-16-14_1_0321072E--01-16-14_17009872_06.jpg']
      // },
      // "pen-tool-roi-test": {
      //   "numOfRois": 4,
      //   "rois": [
      //     'ARE2/workspace/221001_1255845671/output_p/17009872/0321072E--01-16-14_pen-tool-roi-test_0321072E--01-16-14_17009872_01.jpg',
      //     'ARE2/workspace/221001_1255845671/output_p/17009872/0321072E--01-16-14_pen-tool-roi-test_0321072E--01-16-14_17009872_02.jpg',
      //     'ARE2/workspace/221001_1255845671/output_p/17009872/0321072E--01-16-14_pen-tool-roi-test_0321072E--01-16-14_17009872_03.jpg',
      //     'ARE2/workspace/221001_1255845671/output_p/17009872/0321072E--01-16-14_pen-tool-roi-test_0321072E--01-16-14_17009872_04.jpg'
      //   ]
      // }
    },
    processing: true,
    year: new Date().getFullYear()
  }),
  methods: {
    redirect(url) {
      window.location.href = url
    },
    render() {
      this.processing = false;
      this.$api.base.record(this.$props['id']).then((e) => {
          this.link = sanitizeUrl(e.data.link);
          this.lineFileLink = sanitizeUrl(e.data.lineFileLink);
          this.size = e.data.size;
          this.numberOfRoIs = e.data.numberOfRoIs;
          this.processTime = e.data.numberOfRoIs.processTime;
          // this.images = e.images;
      });
      this.$api.base.images(this.$props['id']).then((e) => {
          this.images = e.data;
      });
    },
    changeImageId(e) {
      this.selectedImage = e.target.getAttribute('value');
      this.selectedImageIndex = e.target.id;
      this.$api.base.layerAndROIs(this.selectedImageIndex).then((e) =>{
            this.selectedImageROI = e.data;
        });
    },
    show(e) {
      var options = { index: e.target.parentNode, event: e }
      var links = e.target.parentNode.parentNode.childNodes
      Gallery(links, options)
    }
  },
  mounted() {
    this.processing = true;
    this.referenceId = this.$props['id'];
    // this.render();
    let self = this;
    // const reportSocket = new WebSocket(
    //     'wss://'
    //     + window.location.host
    //     + '/api/w1/message/' + this.$props['id'] + '/'
    // );
    console.log(ws)
    const reportSocket = new WebSocket(
      ws  + '/' + this.$props['id'] + '/'
    );
    reportSocket.onmessage = function(e) {
      self.reports.push(e.data);
      if (e.data == 'Finish') {
        reportSocket.close();
        self.render();
      }
    };

    reportSocket.onclose = function() {
      console.error('Chat socket closed unexpectedly');
    };
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style>
.download {
  color: white !important;
  font-size: 10px;
  text-decoration: none;
}
#links img {
    border: 1px solid #008cba;
    margin: 3px;
    height: 100px;
}
</style>

