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
        meta: { title: "Home" },
    },
    {
        path: "/create-patient",
        name: "CreatePatient",
        component: CreatePatients,
        meta: { title: "New Patient" },
    },
    {
        path: "/search-patients",
        name: "SearchPatients",
        component: SearchPatients,
        meta: { title: "Search Patients" },
    },
    {
        path: "/prediction/:patient_id",
        name: "Prediction",
        component: Prediction,
        meta: { title: "Prediction" },
    },
    {
        path: "/prediction-home",
        name: "PredictionsHome",
        component: PredictionsHome,
        meta: { title: "Predictions" },
    },
    {
        path: "/patient-detail/:id",
        name: "PatientDetail",
        component: PatientDetails,
        meta: { title: "Patient Details" },
    },
    {
        path: "/patient-detail/:id/edit",
        name: "UpdatePatient",
        component: CreatePatients,
        meta: { title: "Edit Patient" },
    },
    {
        path: "/:pathMatch(.*)*",
        name: "NotFound",
        component: NotFound,
        meta: { title: "Not Found" },
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

const APP_NAME = "HEAR-UI";

router.afterEach((to) => {
    const title = to.meta?.title as string | undefined;
    document.title = title ? `${title} | ${APP_NAME}` : APP_NAME;
});

export default router;
