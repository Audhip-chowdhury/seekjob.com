import { Navigate, Route, Routes } from "react-router-dom";
import Landing from "./pages/Landing";
import JobList from "./pages/JobList";
import JobDetail from "./pages/JobDetail";
import ApplicantLogin from "./pages/ApplicantLogin";
import ApplicantRegister from "./pages/ApplicantRegister";
import CompanyLogin from "./pages/CompanyLogin";
import CompanyRegister from "./pages/CompanyRegister";
import Discussions from "./pages/Discussions";
import DiscussionThread from "./pages/DiscussionThread";
import ApplicantDashboard from "./pages/ApplicantDashboard";
import CompanyDashboard from "./pages/CompanyDashboard";
import CompanyApplications from "./pages/CompanyApplications";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/jobs" element={<JobList />} />
      <Route path="/jobs/:id" element={<JobDetail />} />
      <Route path="/login/applicant" element={<ApplicantLogin />} />
      <Route path="/register/applicant" element={<ApplicantRegister />} />
      <Route path="/login/company" element={<CompanyLogin />} />
      <Route path="/register/company" element={<CompanyRegister />} />
      <Route path="/discussions" element={<Discussions />} />
      <Route path="/discussions/:id" element={<DiscussionThread />} />
      <Route path="/applicant/applications" element={<ApplicantDashboard />} />
      <Route path="/company/create-job" element={<CompanyDashboard />} />
      <Route path="/company/applications" element={<CompanyApplications />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
