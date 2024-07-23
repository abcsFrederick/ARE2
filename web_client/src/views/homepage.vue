<template>
  <v-app>
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
            <h3>Imaging and Visualization Group<br>Advanced Biomedical Computing Center</h3>
          </v-flex>
          <v-flex xs8>
            <h4>Description</h4>
            <p>This website extracts sub-images defined on Aperio SVS images and saves these sub-images to separate TIFF image files for downloading. Please read the instructions below and then select the appropriate workflow.</p>
            <h4>Instructions</h4>
            <p>For optimum performance, please use Google Chrome or Mozilla Firefox to display the web site.</p>
            <v-flex xs12 class="well well-sm">
              <h4><a data-toggle="modal" data-target="#workflowOne"><v-icon>mdi-upload</v-icon> Workflow One: Upload Index File (CSV)</a></h4>
              <p>The first way uploads slide data as a list. To use it, navigate to the desired slides in the Spectrum database. Then, select the slides you want and click "Export Data". Next, select "Comma Delimiter" (the default),  click export, and the slide information will be saved on your computer as a CSV file. Then upload the CSV file to the new extraction website using workflow #1.</p>
              <p>About the CSV file, External IDs, Tissue, Tissue Comments, etc. can be edited as needed, and additional information can be added below the slide data. Please do not edit the column titles in row one; the web site needs them. Blank cells will be ignored,  with two exceptions: if a slide’s image ID or file location are missing then the slide will be skipped.</p>
            </v-flex>
          </v-flex>
          <v-flex xs4>
            <v-flex xs12 class="well well-sm">
              <p class="lead">Select Workflow:</p>
              <template>
                <div>
                  <v-dialog
                    v-model="dialog"
                    width="500"
                  >
                    <template v-slot:activator="{ on, attrs }">
                      <v-btn
                        color="primary"
                        dark
                        v-bind="attrs"
                        v-on="on"
                      >
                        <span aria-hidden="true">
                          <v-icon>mdi-upload</v-icon>
                        </span> Workflow One
                      </v-btn>
                    </template>

                    <v-card>
                      <v-card-title class="text-h7 grey lighten-2">
                        Workflow One: Upload Index File (CSV)
                      </v-card-title>

                      <v-card-text>
                        <v-col cols="12">
                          <v-file-input
                            label="Spectrum Exported Index file(CSV)"
                            v-model="fileToUpload"
                          ></v-file-input>
                        </v-col>
                        <v-col cols="12">
                          <v-text-field
                            v-model="username"
                            label="Username"
                            required
                          ></v-text-field>
                        </v-col>
                        <v-col cols="12">
                          <v-text-field
                            v-model="password"
                            label="Password*"
                            type="password"
                            required
                          ></v-text-field>
                        </v-col>
                      </v-card-text>

                      <v-divider></v-divider>

                      <v-card-actions>
                        <v-spacer></v-spacer>
                        <v-btn
                          color="blue darken-1"
                          text
                          @click="dialog = false"
                        >
                          Cancel
                        </v-btn>
                        <v-btn
                          color="primary"
                          @click="submit"
                        >
                          Submit
                        </v-btn>
                      </v-card-actions>
                    </v-card>
                  </v-dialog>
                </div>
              </template>

            </v-flex>
            <v-flex xs12 class="well well-sm">
              <p class="lead">ROI Extraction Statistics:</p>
              <v-btn 
                class="btn btn-primary btn-lg btn-block" 
                data-toggle="modal" 
                data-target="#stats"
              >
                <span aria-hidden="true">
                  <v-icon>mdi-upload</v-icon>
                </span> View Statistics
              </v-btn>
            </v-flex>
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

export default {
  name: 'home',
  data: () => ({
    fileToUpload: [],
    dialog: false,
    username: '',
    password: '',
    year: new Date().getFullYear(),
    smallScreen: false,
    samples: [{   
        label: 'CD4+',
        image: require('../assets/logo.png'),
        description: 'CD4+ workflow description',
        url: 'http://fr-s-ivg-histomics:8080/histomics'
      },
      {   
        label: 'RNAScope',
        image: require('../assets/logo.png'),
        description: 'RNAScope workflow description',
        url: 'http://fr-s-ivg-histomics:8090/RNAScope'
      },
    ],
  }),
  methods: {
    submit() {
      this.dialog = false;
      this.$api.base.submit(this.fileToUpload, this.username, this.password).then((e) => {
        let uid = e.data.uid;
        this.$router.push({ name: 'workflow1', params: {id: uid }})
      });
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style>

.page-header {
  border-bottom: 1px solid #dddddd;
  font-size: 26px 
}

.well {
  min-height: 20px;
  padding: 19px;
  margin-bottom: 20px;
  background-color: #fafafa;
  border: 1px solid #e8e8e8;
}
.root {
  display: flex;
  flex-flow: column;
  height: 100%;
  overflow-y: auto;
}

.buttonText {
  margin-right: 8px;
  text-transform: uppercase;
}

.workflows {
  flex: 1;
  border-radius: 5px;
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23);
}

.linkOverlay {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 100%;
  z-index: 1;
  opacity: 0;
  background: rgba(255,255,255,0.2);
  font-size: 300%;
  text-align: center;
  font-weight: bolder;
  cursor: pointer;
  color: white;
}

.linkOverlay:hover {
  opacity: 1;
}

.description {
  font-size: 80%;
  color: lightgray;
}

.linkOverlayText {
  position: absolute;
  bottom: 0px;
  width: 100%;
  background: rgba(0,0,0,0.4);
  padding: 10px;
}

.copy {
  text-align: right;
  background-color: #f5f5f500;
}
</style>

