// src/router/index.ts
import {createRouter, createWebHistory, RouteRecordRaw} from "vue-router";
import HomePage from "@/routes/HomePage.vue";

const CreatePatients = () => import("@/routes/CreatePatients.vue");
const SearchPatients = () => import("@/routes/SearchPatients.vue");
const Prediction = () => import("@/routes/Prediction.vue");
const PatientDetails = () => import("@/routes/PatientDetails.vue");
const PredictionsHome = () => import("@/routes/PredictionsHome.vue");
const NotFound = () => import("@/routes/NotFound.vue");

const routes: RouteRecordRaw[] = [
    {
        path: "/",
        redirect: "/home", // when opening the app, go to /home
    },
    {
        path: "/home",
        name: "Home",
        component: HomePage,
    },
    {
        path: "/create-patient",
        name: "CreatePatient",
        component: CreatePatients,
    },
    {
        path: "/search-patients",
        name: "SearchPatients",
        component: SearchPatients,
    },
    {
        path: "/prediction/:patient_id",
        name: "Prediction",
        component: Prediction,
    },
    {
        path: "/prediction-home",
        name: "PredictionsHome",
        component: PredictionsHome,
    },
    {
        path: "/patient-detail/:id",
        name: "PatientDetail",
        component: PatientDetails,
    },
    {
        path: "/patient-detail/:id/edit",
        name: "UpdatePatient",
        component: CreatePatients,
    },
    {
        path: "/:pathMatch(.*)*",
        name: "NotFound",
        component: NotFound,
    },
];

const router = createRouter({
    history: createWebHistory(),
    routes,
    scrollBehavior() {
        // Always scroll to the top of the page on every navigation
        return { top: 0, behavior: 'instant' }
    },
});

export default router;
