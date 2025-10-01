

<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced CDA Display - Diana Ferreira</title>

    <!-- CLEAN CSS ARCHITECTURE - September 20, 2025 -->
    <!-- External Dependencies (DMZ Compliant) -->
    <link href="/static/vendor/bootstrap/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="/static/vendor/fontawesome/fontawesome.min.css">

    <!-- All Custom Styles - Compiled from SASS -->
    <link href="/static/css/main.css?v=1759182954" rel="stylesheet" media="screen">

    <!-- PWA Configuration -->
    <link rel="manifest" href="/static/manifest.json">
    <meta name="theme-color" content="#005eb8">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="EU NCP Portal">
    <link rel="apple-touch-icon" href="/static/icons/icon-192x192.png">
    <meta name="msapplication-TileColor" content="#005eb8">
    <meta name="msapplication-TileImage" content="/static/icons/icon-144x144.png">




</head>

<body>
    <!-- Professional Medical Portal Navigation Bar - Hidden on Home Page -->

    <nav id="main-navigation" class="navbar navbar-expand-lg navbar-light navbar-enhanced" role="navigation" aria-label="Main navigation">
        <div class="container-fluid px-4">
            <!-- Skip to main content link for accessibility -->
            <a href="#main-content" class="visually-hidden-focusable btn btn-primary">Skip to main content</a>

            <!-- Enhanced Brand with Professional Medical Identity -->
            <a href="/" class="navbar-brand d-flex align-items-center" aria-label="EU NCP Portal - International Medical Portal Home">
                <i class="fa-solid fa-hospital-user text-primary fa-2xl" aria-hidden="true" title="Medical Portal"></i>
                <span class="fw-bold text-primary">
                    <span class="brand-primary">EU NCP</span>
                    <span class="brand-secondary">Home</span>
                </span>
            </a>

            <!-- Enhanced Mobile toggle button -->
            <button class="navbar-toggler border-0" type="button" data-bs-toggle="collapse" data-bs-target="#navbar-nav"
                    aria-controls="navbar-nav" aria-expanded="false" aria-label="Toggle navigation menu">
                <span class="navbar-toggler-icon"></span>
            </button>

            <!-- Professional Medical Navigation with Logical Grouping -->
            <div class="collapse navbar-collapse" id="navbar-nav">
                <ul class="navbar-nav me-auto mb-2 mb-lg-0" role="menubar">
                    <!-- Primary Navigation Group -->
                    <li class="nav-item nav-group-primary" role="none">
                        <a href="/patients/search/" class="nav-link active"
                           role="menuitem" aria-current="page">
                            <i class="fa-solid fa-user-md fa-1xl" aria-hidden="true" title="Patient Search"></i>
                            <span>Patient Search</span>
                        </a>
                    </li>
                    <li class="nav-item nav-group-primary nav-group-end" role="none">
                        <a href="/portal/" class="nav-link "
                           role="menuitem" aria-current="">
                            <i class="fa-solid fa-globe-europe fa-1xl" aria-hidden="true" title="European Portal"></i>
                            <span>Portal</span>
                        </a>
                    </li>

                    <!-- Management Group - Role-Based Access -->

                    <li class="nav-item nav-group-management dropdown" role="none">
                        <a href="/smp/" class="nav-link dropdown-toggle "
                           role="button" data-bs-toggle="dropdown" aria-expanded="false"
                           aria-haspopup="true" aria-label="SMP Management Menu">
                            <i class="fa-solid fa-network-wired fa-1xl" aria-hidden="true" title="Secure Message Protocol"></i>
                            <span>SMP Management</span>
                        </a>
                        <ul class="dropdown-menu mega-menu" aria-label="SMP Management submenu">
                            <li><h6 class="dropdown-header">
                                <i class="fa-solid fa-shield-alt fa-2xl" aria-hidden="true"></i>
                                Security & Protocols
                            </h6></li>
                            <li><a class="dropdown-item" href="/smp/certificates/">
                                <i class="fa-solid fa-certificate fa-2xl" aria-hidden="true"></i>
                                Certificate Management
                            </a></li>
                            <li><a class="dropdown-item" href="/smp/endpoints/">
                                <i class="fa-solid fa-plug fa-2xl" aria-hidden="true"></i>
                                Service Endpoints
                            </a></li>


                            <li><hr class="dropdown-divider"></li>
                            <li><h6 class="dropdown-header">
                                <i class="fa-solid fa-chart-line fa-2xl" aria-hidden="true"></i>
                                Advanced Monitoring <span class="badge bg-secondary">Admin</span>
                            </h6></li>
                            <li><a class="dropdown-item" href="/smp/logs/">
                                <i class="fa-solid fa-clipboard-list fa-2xl" aria-hidden="true"></i>
                                System Logs
                            </a></li>
                            <li><a class="dropdown-item" href="/smp/performance/">
                                <i class="fa-solid fa-tachometer-alt fa-2xl" aria-hidden="true"></i>
                                Performance Metrics
                            </a></li>
                            <li><a class="dropdown-item" href="/smp/audit/">
                                <i class="fa-solid fa-search fa-2xl" aria-hidden="true"></i>
                                Audit Trail
                            </a></li>

                        </ul>
                    </li>


                    <li class="nav-item nav-group-management nav-group-end dropdown" role="none">
                        <a href="/admin/" class="nav-link dropdown-toggle "
                           role="button" data-bs-toggle="dropdown" aria-expanded="false"
                           aria-haspopup="true" aria-label="System Administration Menu">
                            <i class="fa-solid fa-cogs fa-1xl" aria-hidden="true" title="System Administration"></i>
                            <span>Admin</span>
                            <span class="badge bg-warning text-dark ms-1">Power User</span>
                        </a>
                        <ul class="dropdown-menu mega-menu" aria-label="System Administration submenu">
                            <li><h6 class="dropdown-header">
                                <i class="fa-solid fa-users-cog fa-2xl" aria-hidden="true"></i>
                                User Management
                            </h6></li>
                            <li><a class="dropdown-item" href="/admin/auth/user/">
                                <i class="fa-solid fa-users fa-2xl" aria-hidden="true"></i>
                                User Accounts
                            </a></li>
                            <li><a class="dropdown-item" href="/admin/auth/group/">
                                <i class="fa-solid fa-user-tag fa-2xl" aria-hidden="true"></i>
                                User Groups & Permissions
                            </a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><h6 class="dropdown-header">
                                <i class="fa-solid fa-database fa-2xl" aria-hidden="true"></i>
                                System Configuration
                            </h6></li>
                            <li><a class="dropdown-item" href="/admin/sites/site/">
                                <i class="fa-solid fa-globe fa-2xl" aria-hidden="true"></i>
                                Site Settings
                            </a></li>
                            <li><a class="dropdown-item" href="/admin/sessions/session/">
                                <i class="fa-solid fa-clock fa-2xl" aria-hidden="true"></i>
                                Active Sessions
                            </a></li>

                            <li><hr class="dropdown-divider"></li>
                            <li><h6 class="dropdown-header">
                                <i class="fa-solid fa-shield-alt fa-2xl" aria-hidden="true"></i>
                                Super Admin <span class="badge bg-danger">Restricted</span>
                            </h6></li>
                            <li><a class="dropdown-item" href="/admin/django_admin_log/logentry/">
                                <i class="fa-solid fa-history fa-2xl" aria-hidden="true"></i>
                                Admin Activity Log
                            </a></li>
                            <li><a class="dropdown-item" href="/admin/contenttypes/">
                                <i class="fa-solid fa-code fa-2xl" aria-hidden="true"></i>
                                Content Types
                            </a></li>

                        </ul>
                    </li>


                </ul>

                <!-- Enhanced Authentication Status with Professional Design -->
                <div class="d-flex align-items-center" role="region" aria-label="User authentication status">

                    <div class="d-flex align-items-center">
                        <span class="text-muted me-3" role="status" aria-live="polite">
                            <i class="fa-solid fa-user-circle fa-1xl" aria-hidden="true" title="Authenticated User"></i>
                            <span class="visually-hidden">Logged in as </span>
                            <span class="user-welcome">Welcome, <strong>admin</strong></span>
                        </span>
                        <a href="/accounts/logout/" class="btn btn-outline-primary btn-sm"
                           title="Sign out of your account" aria-label="Logout from EU NCP Portal">
                            <i class="fa-solid fa-sign-out-alt fa-1xl" aria-hidden="true"></i>
                            <span>Logout</span>
                        </a>
                    </div>

                </div>
            </div>
        </div>
    </nav>


    <!-- Power User Sidebar for Admin/Staff Users -->

    <aside class="power-user-sidebar" id="powerUserSidebar" aria-label="Power User Quick Access">
        <button class="sidebar-toggle" type="button" aria-label="Toggle Power User Sidebar" title="Quick Access Panel">
            <i class="fa-solid fa-tools" aria-hidden="true"></i>
        </button>

        <div class="sidebar-content">
            <div class="sidebar-header">
                <h6 class="sidebar-title">
                    <i class="fa-solid fa-crown fa-2xl" aria-hidden="true"></i>
                    Quick Access

                    <span class="badge bg-danger fa-2xl">Super Admin</span>

                </h6>
            </div>

            <nav class="sidebar-nav" role="navigation" aria-label="Quick access navigation">
                <div class="nav-section">
                    <h6 class="nav-section-title">
                        <i class="fa-solid fa-tachometer-alt fa-2xl" aria-hidden="true"></i>
                        System Monitor
                    </h6>
                    <ul class="nav-list">
                        <li><a href="/admin/django_admin_log/logentry/" class="nav-item">
                            <i class="fa-solid fa-history fa-2xl" aria-hidden="true"></i>
                            <span>Recent Activity</span>
                        </a></li>
                        <li><a href="/admin/sessions/session/" class="nav-item">
                            <i class="fa-solid fa-users-cog fa-2xl" aria-hidden="true"></i>
                            <span>Active Sessions</span>
                        </a></li>
                        <li><a href="/smp/performance/" class="nav-item">
                            <i class="fa-solid fa-chart-line fa-2xl" aria-hidden="true"></i>
                            <span>Performance</span>
                        </a></li>
                    </ul>
                </div>

                <div class="nav-section">
                    <h6 class="nav-section-title">
                        <i class="fa-solid fa-users fa-2xl" aria-hidden="true"></i>
                        User Management
                    </h6>
                    <ul class="nav-list">
                        <li><a href="/admin/auth/user/" class="nav-item">
                            <i class="fa-solid fa-user-plus fa-2xl" aria-hidden="true"></i>
                            <span>Add Users</span>
                        </a></li>
                        <li><a href="/admin/auth/group/" class="nav-item">
                            <i class="fa-solid fa-user-tag fa-2xl" aria-hidden="true"></i>
                            <span>Manage Groups</span>
                        </a></li>
                    </ul>
                </div>


                <div class="nav-section">
                    <h6 class="nav-section-title">
                        <i class="fa-solid fa-shield-alt fa-2xl" aria-hidden="true"></i>
                        Super Admin
                    </h6>
                    <ul class="nav-list">
                        <li><a href="/admin/sites/site/" class="nav-item">
                            <i class="fa-solid fa-globe fa-2xl" aria-hidden="true"></i>
                            <span>Site Settings</span>
                        </a></li>
                        <li><a href="/admin/contenttypes/" class="nav-item">
                            <i class="fa-solid fa-code fa-2xl" aria-hidden="true"></i>
                            <span>Content Types</span>
                        </a></li>
                    </ul>
                </div>

            </nav>
        </div>
    </aside>


    <!-- Page Breadcrumb/Context Area -->

<div class="page-context-content">
    <div class="page-info">
        <span class="page-location">
            <i class="fa fa-file-medical"></i> CDA Document
        </span>
    </div>
    <div class="page-actions">

        <a href="/patients/smart-search/2624725854/"
            class="btn btn-outline-secondary btn-sm">
            <i class="fa fa-arrow-left page-action-icon"></i> Back to Patient
        </a>

    </div>
</div>



    <!-- Main Content Area -->
    <main id="main-content" class="container-fluid py-4" role="main" aria-label="Main content">



<div class="p-0">
    <!-- Patient Header with Tabbed Interface -->
    <div class="section-wrapper">
        <!-- Main Patient Header Card with Integrated Tabs -->
        <div class="card shadow">
            <div class="card-header bg-primary text-white">
                <div class="d-flex justify-content-between align-items-center">
                    <h2 class="mb-0" data-bs-toggle="tooltip" data-bs-placement="bottom" title="Primary patient identification extracted from the Clinical Document Architecture. May include given name, family name, and patient identifiers from the source healthcare system.">
                        <i class="fa-solid fa-user-injured me-2"></i>


                        Diana Ferreira

                    </h2>
                    <div class="d-flex align-items-center">
                        <span class="badge bg-light text-dark border me-2"
                              data-bs-toggle="tooltip" data-bs-placement="bottom" title="Shows the country where this Clinical Document Architecture (CDA) was originally created. Detected automatically from document language code, custodian organization name, or patient address information.">
                            <img src="/static/flags/PT.webp" alt="Portugal" class="flag-img" width="20" height="15" style="margin-right: 5px;">
                            Portugal
                        </span>
                        <span class="badge bg-success"
                              data-bs-toggle="tooltip" data-bs-placement="bottom" title="Indicates the level of structured data extraction success. &quot;High&quot; means enhanced JSON field mapping is active and structured medical data was successfully extracted from the CDA document. &quot;Basic&quot; indicates standard text extraction only.">
                            <i class="fa-solid fa-check-circle me-1"></i>High
                        </span>
                    </div>
                </div>
            </div>

            <!-- Integrated Navigation Tabs -->
            <div class="card-body p-0">
                <ul class="nav nav-tabs nav-tabs-healthcare border-0" id="patientTabs" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link active" id="overview-tab" data-bs-toggle="tab"
                            data-bs-target="#overview-content" type="button" role="tab"
                            aria-controls="overview-content" aria-selected="true">
                            <i class="fa-solid fa-user me-2"></i>
                            Patient Overview
                        </button>
                    </li>

                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="extended-tab" data-bs-toggle="tab"
                            data-bs-target="#extended-content" type="button" role="tab"
                            aria-controls="extended-content" aria-selected="false">
                            <i class="fa-solid fa-user-plus me-2"></i>
                            Extended Patient Information
                        </button>
                    </li>
                </ul>

                <!-- Integrated Tab Content -->
                <div class="tab-content" id="patientTabContent">
                    <!-- Patient Overview Tab Content -->
                    <div class="tab-pane fade show active" id="overview-content" role="tabpanel" aria-labelledby="overview-tab">
                        <div class="p-4">
                            <div class="row">
                                <div class="col-md-6">
                                    <p><i class="fa-solid fa-calendar text-info me-1"></i>
                                        <strong>Birth Date:</strong>

                                        08/05/1982

                                    </p>
                                    <p><i class="fa-solid fa-venus-mars text-info me-1"></i>
                                        <strong>Gender:</strong> female</p>
                                    <p><i class="fa-solid fa-fingerprint text-info me-1"></i>
                                        <strong>Patient ID:</strong>
                                        2-1234-W7</p>


                                    <p><i class="fa-solid fa-fingerprint text-info me-1"></i>
                                        <strong>Additional ID:</strong>
                                        2-1234-W7</p>






                                        <span class="text-secondary-accessible">
                                            <i class="fa-solid fa-key me-1"></i>
                                            <strong>Root ID:</strong>
                                            2.16.17.710.850.1000.990.1.1000
                                        </span>


                                </div>
                                <div class="col-md-6">
                                    <p><strong>Source Country:</strong>
                                        <img src="/static/flags/PT.webp" alt="Portugal" class="flag-img" width="20" height="15" style="margin-right: 5px;">
                                        Portugal
                                    </p>
                                    <p><strong>CDA Type:</strong> L3</p>
                                    <p><strong>Translation Quality:</strong>
                                        <span class="badge bg-success"
                                              data-bs-toggle="tooltip" data-bs-placement="bottom" title="Indicates the level of structured data extraction success. &quot;High&quot; means enhanced JSON field mapping is active and structured medical data was successfully extracted from the CDA document. &quot;Basic&quot; indicates standard text extraction only.">
                                            High
                                        </span>
                                    </p>



                                    <p><strong>Document:</strong> Patient Summary</p>


                                    <p><strong>Language:</strong> en-GB</p>


                                </div>
                            </div>

                            <!-- CDA Type Toggle Buttons -->
                            <div class="row mt-3">
                                <div class="col-12">
                                    <div class="btn-group" role="group" aria-label="CDA Type Selection">


                                        <a href="/patients/cda/2624725854/L1/"
                                            class="btn btn-outline-primary  disabled">
                                            <i class="fa-solid fa-file-medical me-1"></i>L1 Original Document
                                            <small>(Not Available)</small>
                                        </a>

                                        <a href="/patients/cda/2624725854/L3/"
                                            class="btn btn-primary ">
                                            <i class="fa-solid fa-language me-1"></i>L3 Patient Summary

                                        </a>

                                    </div>
                                    <small class="text-muted d-block mt-1">
                                        <strong>L1:</strong> Original clinical document from source country |
                                        <strong>L3:</strong> Standardized European Patient Summary

                                        | Currently viewing: <strong>European Patient Summary</strong>

                                    </small>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Extended Patient Information Tab Content -->
                    <div class="tab-pane fade" id="extended-content" role="tabpanel" aria-labelledby="extended-tab">
                        <div class="p-4">





<div class="clinical-section" id="extendedPatientSection" data-patient-id="">
    <!-- Tab Navigation Buttons -->
    <div class="tab-navigation mb-3">
        <button class="tab-button active" data-action="show-extended-tab" data-section-id="extended_patient" data-tab-type="personal"
                type="button">
            <i class="fa-solid fa-user me-1"></i>Personal Information


            <span class="badge bg-primary ms-2">






                    2




            </span>

        </button>

        <button class="tab-button" data-action="show-extended-tab" data-section-id="extended_patient" data-tab-type="healthcare"
                type="button">
            <i class="fa-solid fa-stethoscope me-1"></i>Healthcare Team

            <span class="badge bg-success ms-2">1</span>

        </button>

        <button class="tab-button" data-action="show-extended-tab" data-section-id="extended_patient" data-tab-type="system"
                type="button">
            <i class="fa-solid fa-server me-1"></i>System & Documentation
            <span class="badge bg-warning ms-2">3</span>
        </button>

        <button id="clinical-tab-btn" class="tab-button"
                data-action="show-extended-tab"
                data-section-id="extended_patient"
                data-tab-type="clinical"

                type="button"
                >
            <i class="fa-solid fa-notes-medical me-1"></i>Clinical Information
            <!-- DEBUG: med=0 all=0 prob=0 vs=0 proc=0 -->
            <!-- DEBUG: has_l1_cda=False has_l3_cda=True processed_sections=13 -->

            <span class="badge bg-info ms-2">13</span>

        </button>

        <button id="pdf-tab-btn" class="tab-button text-muted"
                data-action="show-extended-tab"
                data-section-id="extended_patient"
                data-tab-type="pdfs"
                data-disabled="true" data-reason="No Original Clinical Documents available for this L3 CDA"
                type="button"
                disabled title="No Original Clinical Documents available for this L3 CDA">
            <i class="fa-solid fa-file-pdf me-1"></i>Original Clinical Document

            <span class="badge bg-secondary ms-2">0</span>

        </button>
    </div>


    <div class="extended-tab-content-container clinical-tabs-container">


    <div class="clinical-tab-content active" id="extended_patient_personal">












<div class="contact-info-grid">
    <div class="row g-3">


        <div class="col-12 col-md-6 col-lg-4">
            <div class="card service-card border-info h-100">
                <div class="card-header bg-info text-white">
                    <h6 class="mb-0">
                        <i class="fa-solid fa-user me-2"></i>Patient Demographics
                    </h6>
                </div>
                <div class="card-body d-flex flex-column">

                    <div class="mb-2">
                        <strong class="text-secondary-accessible">
                            Diana Ferreira
                        </strong>
                    </div>


                    <div class="flex-grow-1">

                        <div class="mb-2">
                            <small class="text-secondary-accessible">
                                <i class="fa-solid fa-calendar text-info me-1"></i>
                                <strong>Birth Date:</strong>
                                19820508
                            </small>
                        </div>



                        <div class="mb-2">
                            <span class="text-secondary-accessible">
                                <i class="fa-solid fa-venus-mars text-info me-1"></i>
                                <strong>Gender:</strong>
                                Female
                            </span>
                        </div>



                        <div class="mb-2">
                            <span class="text-secondary-accessible">
                                <i class="fa-solid fa-fingerprint text-info me-1"></i>
                                <strong>Patient ID:</strong>
                                <small>2-1234-W7</small>




                                    <br><span class="text-secondary-accessible">
                                        <i class="fa-solid fa-key me-1"></i>
                                        <strong>Root ID:</strong>
                                        2.16.17.710.850.1000.990.1.1000
                                    </span>


                            </span>
                        </div>

                    </div>
                </div>
            </div>
        </div>







        <div class="col-12 col-md-6 col-lg-4">
            <div class="card service-card border-primary h-100">
                <div class="card-header bg-primary text-white">
                    <h6 class="mb-0">
                        <i class="fa-solid fa-map-marker-alt me-2"></i>Patient Address
                    </h6>
                </div>
                <div class="card-body d-flex flex-column">


                        <div class="mb-2 flex-grow-1">
                            <small class="text-secondary-accessible">

                                    155, Avenida da Liberdade


                                    <br>
                                    Lisbon, 1250-141<br>Portugal

                            </small>
                        </div>



                </div>
            </div>
        </div>




        <div class="col-12 col-md-6 col-lg-4">
            <div class="card service-card border-info h-100">
                <div class="card-header bg-info text-white">
                    <h6 class="mb-0">
                        <i class="fa-solid fa-phone me-2"></i>Contact Methods
                    </h6>
                </div>
                <div class="card-body d-flex flex-column">


                        <div class="mb-2">
                            <div class="d-flex align-items-center">

                                <i class="fa-solid fa-phone text-info me-2"></i>

                                <small class="text-secondary-accessible flex-grow-1">
                                    <strong>351211234567</strong>
                                    <br><em>H</em>
                                </small>
                            </div>
                        </div>
                        <hr class="my-2">

                        <div class="mb-2">
                            <div class="d-flex align-items-center">

                                <i class="fa-solid fa-envelope text-info me-2"></i>

                                <small class="text-secondary-accessible flex-grow-1">
                                    <strong>paciente@gmail.com</strong>

                                </small>
                            </div>
                        </div>



                </div>
            </div>
        </div>






        <div class="col-12 col-md-6 col-lg-4">
            <div class="card service-card border-warning h-100">
                <div class="card-header bg-warning text-dark">
                    <h6 class="mb-0">
                        <i class="fa-solid fa-user-shield me-2"></i>Guardian / Next of Kin
                    </h6>
                </div>
                <div class="card-body d-flex flex-column">
                    <div class="mb-2">
                        <strong class="text-secondary-accessible">
                            Joaquim Baptista
                        </strong>

                        <br><span class="badge bg-info">Guardian</span>

                    </div>


                    <div class="flex-grow-1">


                        <div class="mb-2">
                            <small class="text-secondary-accessible">
                                <i class="fa-solid fa-map-marker-alt text-warning me-1"></i>
                                155, Avenida da Liberdade
                                <br>Lisbon
                                 1250-141
                                <br>
                                Portugal

                            </small>
                        </div>





                        <div class="mb-1">
                            <small class="text-secondary-accessible">

                                <i class="fa-solid fa-envelope text-warning me-1"></i>

                                guardian@gmail.com
                            </small>
                        </div>

                        <div class="mb-1">
                            <small class="text-secondary-accessible">

                                <i class="fa-solid fa-phone text-warning me-1"></i>

                                351211234569
                            </small>
                        </div>


                    </div>

                </div>
            </div>
        </div>






        <div class="col-12 col-md-6 col-lg-4">
            <div class="card service-card border-secondary h-100">
                <div class="card-header bg-secondary text-white">
                    <h6 class="mb-0">
                        <i class="fa-solid fa-users me-2"></i>Emergency Contact
                    </h6>
                </div>
                <div class="card-body d-flex flex-column">
                    <div class="mb-2">
                        <strong class="text-secondary-accessible">
                            Vitória Silva
                        </strong>

                        <br><span class="badge bg-info">Contact Person</span>

                    </div>


                    <div class="flex-grow-1">


                        <div class="mb-2">
                            <small class="text-secondary-accessible">
                                <i class="fa-solid fa-map-marker-alt text-secondary me-1"></i>
                                147, Rua Augusta
                                <br>Lisbon
                                 1100-049
                                <br>
                                Portugal

                            </small>
                        </div>





                        <div class="mb-1">
                            <small class="text-secondary-accessible">

                                <i class="fa-solid fa-envelope text-secondary me-1"></i>

                                paciente@gmail.com
                            </small>
                        </div>

                        <div class="mb-1">
                            <small class="text-secondary-accessible">

                                <i class="fa-solid fa-phone text-secondary me-1"></i>

                                351211234570
                            </small>
                        </div>


                    </div>

                </div>
            </div>
        </div>




    </div>
</div>



    </div>


    <div class="clinical-tab-content" id="extended_patient_healthcare">
        <div class="row g-3">

            <div class="col-12">
                <div class="card border-success">
                    <div class="card-header bg-success text-white">
                        <h5 class="mb-0">
                            <i class="fa-solid fa-user-md me-2"></i>Healthcare Provider Information
                        </h5>
                    </div>
                    <div class="card-body">


<!-- Extended Patient Healthcare Team Component -->
<!-- This component provides content for the Healthcare Team tab -->


<!-- Single Unified Healthcare Information Section -->
<div class="healthcare-info-unified">
    <div class="row g-3">
        <!-- Healthcare Provider Information -->


        <div class="col-md-6">
            <div class="healthcare-card h-100">
                <div class="healthcare-header">
                    <i class="fa-solid fa-user-md me-2"></i>
                    <strong>Healthcare Provider</strong>
                </div>
                <div class="healthcare-content">
                    <div class="provider-name">

                        António Pereira

                    </div>








                </div>
            </div>
        </div>



        <!-- Healthcare Organization Information -->


        <div class="col-md-6">
            <div class="healthcare-card h-100">
                <div class="healthcare-header">
                    <i class="fa-solid fa-hospital me-2"></i>
                    <strong>Healthcare Organization</strong>
                </div>
                <div class="healthcare-content">
                    <div class="organization-name">
                        Centro Hospitalar de Lisboa Central
                    </div>




                    <div class="organization-details mt-3">
                        <div class="detail-section-title">Contact Information</div>

                        <div class="provider-telecom">

                            <i class="fa-solid fa-globe text-info me-2"></i>

                            <span class="telecom-value">mailto:hospital@gmail.com</span>
                            <span class="telecom-type">()</span>
                        </div>

                    </div>



                    <div class="organization-details mt-3">
                        <div class="detail-section-title">Organization Address</div>

                        <div class="address-display">

                            <div class="address-location">
                                Lisbon

                                , PT
                            </div>
                        </div>

                    </div>

                </div>
            </div>
        </div>


    </div>

    <!-- Additional Healthcare Information -->

    <div class="row mt-4">
        <div class="col-12">
            <div class="healthcare-card">
                <div class="healthcare-header">
                    <i class="fa-solid fa-certificate me-2"></i>
                    <strong>Legal Authenticator</strong>
                </div>

                <div class="healthcare-content">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="detail-section-title">Authenticator</div>
                            <div class="fw-medium">

                                António Pereira

                            </div>
                        </div>
                        <div class="col-md-6">

                        </div>
                    </div>
                </div>

            </div>
        </div>
    </div>

</div>

                    </div>
                </div>
            </div>
        </div>
    </div>


    <div class="clinical-tab-content" id="extended_patient_system">
        <div class="row g-3">

            <div class="col-12">
                <div class="card border-info">
                    <div class="card-header bg-info text-white">
                        <h5 class="mb-0">
                            <i class="fa-solid fa-cogs me-2"></i>Administrative & System Information
                        </h5>
                    </div>
                    <div class="card-body">


<!-- Extended Patient Document Information Component -->
<!-- This component provides content for the Document Info tab -->


<!-- Single Unified Document Information Section -->
<div class="document-info-unified">
    <div class="row g-3">
        <!-- Document Metadata Section -->
        <div class="col-md-6">
            <div class="document-card h-100">
                <div class="document-header">
                    <i class="fa-solid fa-file-medical-alt me-2"></i>
                    <strong>Document Information</strong>
                </div>
                <div class="document-content">
                    <div class="document-type">
                        Patient Summary (PS)
                        <span class="document-standard">European eHealth Standard</span>
                    </div>

                    <div class="document-details mt-3">
                        <div class="detail-section-title">Document Status</div>
                        <div class="status-badges">
                            <span class="status-badge status-active">Active</span>
                            <span class="status-badge status-secure">Secure</span>
                            <span class="status-badge status-normal">Normal Confidentiality</span>
                        </div>
                    </div>

                    <div class="document-details mt-3">
                        <div class="detail-item">
                            <span class="detail-label">Creation Date:</span>
                            <span class="detail-value">08/06/2022 10:49</span>
                        </div>




                        <div class="detail-item">
                            <span class="detail-label">Document ID:</span>
                            <span class="detail-value">2.999.111</span>
                        </div>

                    </div>
                </div>
            </div>
        </div>

        <!-- Document Custodian Section -->
        <div class="col-md-6">
            <div class="document-card h-100">
                <div class="document-header">
                    <i class="fa-solid fa-shield-alt me-2"></i>
                    <strong>Document Custodian</strong>
                </div>
                <div class="document-content">


                    <div class="custodian-name">
                        Centro Hospitalar de Lisboa Central
                    </div>




                    <div class="custodian-details mt-3">
                        <div class="detail-section-title">Contact Information</div>

                        <div class="custodian-telecom">

                            <i class="fa-solid fa-globe text-info me-2"></i>

                            <span class="telecom-value">mailto:hospital@gmail.com</span>
                            <span class="telecom-type">()</span>
                        </div>

                    </div>



                    <div class="custodian-details mt-3">
                        <div class="detail-section-title">Organization Address</div>

                        <div class="address-display">

                            <div class="address-location">
                                Lisbon

                                , PT
                            </div>
                        </div>

                    </div>



                </div>
            </div>
        </div>
    </div>
</div>


                    </div>
                </div>
            </div>
        </div>
    </div>


    <div class="clinical-tab-content" id="extended_patient_clinical">

        <!-- Clinical Information Content Component -->



<div class="clinical-information-container">
    <!-- Check if we have any clinical data -->


    <!-- Clinical Information Master Controls with View Toggle -->
    <div class="clinical-master-controls mb-3">
        <!-- View Toggle Tabs -->
        <div class="clinical-view-tabs mb-3">
            <ul class="nav nav-tabs" id="clinicalViewTabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="enhanced-tab" data-bs-toggle="tab"
                            data-bs-target="#enhanced-clinical-view" type="button" role="tab"
                            aria-controls="enhanced-clinical-view" aria-selected="true">
                        <i class="fa-solid fa-chart-bar me-1"></i>
                        Enhanced View
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="simplified-tab" data-bs-toggle="tab"
                            data-bs-target="#simplified-clinical-view" type="button" role="tab"
                            aria-controls="simplified-clinical-view" aria-selected="false">
                        <i class="fa-solid fa-table me-1"></i>
                        Simplified View
                    </button>
                </li>
            </ul>
        </div>

        <!-- Controls for Enhanced View Only -->
        <div class="enhanced-controls d-flex justify-content-between align-items-center" id="enhancedViewControls">
            <div class="control-buttons">
                <button type="button" class="btn btn-outline-primary btn-sm me-2" id="expandAllClinical">
                    <i class="fa-solid fa-expand-arrows-alt me-1"></i>
                    Expand All
                </button>
                <button type="button" class="btn btn-outline-secondary btn-sm" id="collapseAllClinical">
                    <i class="fa-solid fa-compress-arrows-alt me-1"></i>
                    Collapse All
                </button>
            </div>
            <div class="section-count text-muted">
                <small>
                    <i class="fa-solid fa-info-circle me-1"></i>
                    Clinical sections can be expanded/collapsed independently
                </small>
            </div>
        </div>
    </div>

    <!-- Tab Content Container -->
    <div class="tab-content" id="clinicalViewTabContent">

        <!-- Enhanced View Tab -->
        <div class="tab-pane fade show active" id="enhanced-clinical-view" role="tabpanel" aria-labelledby="enhanced-tab">
            <!-- Clinical Information Accordion -->
            <div class="accordion" id="clinicalInformationAccordion">

        <!-- Dynamic Clinical Sections from processed_sections -->

        <div class="accordion-item clinical-accordion-item">
            <h2 class="accordion-header" id="heading-1">
                <button class="accordion-button clinical-section-header-optimized" type="button"
                        onclick="toggleSection('collapse-1')"
                        aria-expanded="true"
                        aria-controls="collapse-1">

                    <!-- Left side: Section title and icon -->
                    <div class="section-title-area d-flex align-items-center flex-grow-1">
                        <i class="section-icon fas fa-file-medical text-muted"></i>
                        <div>
                            <strong class="section-title">History of Medication use Narrative</strong>

                            <!-- Enhanced Translation Context -->

                        </div>
                    </div>

                    <!-- Center: Inline Tab Controls (NEW - moved from child) -->
                    <div class="header-tab-controls" onclick="event.stopPropagation();">
                        <button class="header-tab-button active"
                                onclick="showClinicalTab('1', 'structured')"
                                data-section="1"
                                data-tab="structured">
                            <i class="tab-icon fa-solid fa-chart-bar"></i>Structured
                        </button>
                        <button class="header-tab-button"
                                onclick="showClinicalTab('1', 'original')"
                                data-section="1"
                                data-tab="original">
                            <i class="tab-icon fa-solid fa-file-text"></i>Original
                        </button>
                    </div>

                    <!-- Right side: Metrics and controls -->
                    <div class="section-controls-area d-flex align-items-center" onclick="event.stopPropagation();">

                        <!-- Professional Metrics -->
                        <div class="clinical-metrics-compact me-3">


                        </div>

                        <!-- Content Toggle Buttons -->

                    </div>
                </button>
            </h2>
            <div id="collapse-1"
                 class="accordion-collapse collapse show"
                 aria-labelledby="heading-1">
                <div class="accordion-body clinical-accordion-content-optimized">
                    <!-- Optimized Clinical Section Router - No child card wrapper -->




<!-- Render individual clinical section (called within loop from main template) -->

    <!-- Route to specialized section templates based on section type -->


            <!-- Use enhanced template for sections with rich clinical data -->





<!-- Generic Clinical Section - Optimized (no card wrapper) -->
<div class="medical-section"
    id="generic-section">
    <!-- Remove card wrapper - content goes directly in accordion body -->

        <!-- Clinical Section Content with Tabs -->

        <!-- Optimized Text-only Section - Tabs now in parent header -->

            <!-- Original Content Tab -->
            <div id="generic_0_original" class="clinical-tab-content active">



<div class="original-content">
    <h4>Original Clinical Data from NCPeH-A - History of Medication use Narrative</h4>


</div>

            </div>

</div>






<!-- Debug information (development only) -->


                </div>
            </div>
        </div>

        <div class="accordion-item clinical-accordion-item">
            <h2 class="accordion-header" id="heading-2">
                <button class="accordion-button clinical-section-header-optimized" type="button"
                        onclick="toggleSection('collapse-2')"
                        aria-expanded="true"
                        aria-controls="collapse-2">

                    <!-- Left side: Section title and icon -->
                    <div class="section-title-area d-flex align-items-center flex-grow-1">
                        <i class="section-icon fas fa-file-medical text-muted"></i>
                        <div>
                            <strong class="section-title">Allergies and adverse reactions Document</strong>

                            <!-- Enhanced Translation Context -->

                        </div>
                    </div>

                    <!-- Center: Inline Tab Controls (NEW - moved from child) -->
                    <div class="header-tab-controls" onclick="event.stopPropagation();">
                        <button class="header-tab-button active"
                                onclick="showClinicalTab('2', 'structured')"
                                data-section="2"
                                data-tab="structured">
                            <i class="tab-icon fa-solid fa-chart-bar"></i>Structured
                        </button>
                        <button class="header-tab-button"
                                onclick="showClinicalTab('2', 'original')"
                                data-section="2"
                                data-tab="original">
                            <i class="tab-icon fa-solid fa-file-text"></i>Original
                        </button>
                    </div>

                    <!-- Right side: Metrics and controls -->
                    <div class="section-controls-area d-flex align-items-center" onclick="event.stopPropagation();">

                        <!-- Professional Metrics -->
                        <div class="clinical-metrics-compact me-3">


                        </div>

                        <!-- Content Toggle Buttons -->

                    </div>
                </button>
            </h2>
            <div id="collapse-2"
                 class="accordion-collapse collapse show"
                 aria-labelledby="heading-2">
                <div class="accordion-body clinical-accordion-content-optimized">
                    <!-- Optimized Clinical Section Router - No child card wrapper -->




<!-- Render individual clinical section (called within loop from main template) -->

    <!-- Route to specialized section templates based on section type -->





<!-- Allergies and Intolerances Section -->
<div class="medical-section" id="allergies-section">
    <!-- Remove card wrapper - content goes directly in accordion body -->

        <!-- Clinical Section Content with Tabs -->

        <!-- Empty Allergies Section - Optimized (no wrapper) -->
        <div class="text-center py-5">
            <div class="text-success">
                <i class="fa-solid fa-check-circle fa-3x mb-3"></i>
                <h6 class="text-success">No Known Allergies</h6>
                <p class="text-muted">No allergies or adverse reactions reported for this patient</p>
            </div>
        </div>

</div>







<!-- Debug information (development only) -->


                </div>
            </div>
        </div>

        <div class="accordion-item clinical-accordion-item">
            <h2 class="accordion-header" id="heading-3">
                <button class="accordion-button clinical-section-header-optimized" type="button"
                        onclick="toggleSection('collapse-3')"
                        aria-expanded="true"
                        aria-controls="collapse-3">

                    <!-- Left side: Section title and icon -->
                    <div class="section-title-area d-flex align-items-center flex-grow-1">
                        <i class="section-icon fas fa-file-medical text-muted"></i>
                        <div>
                            <strong class="section-title">History of Procedures Document</strong>

                            <!-- Enhanced Translation Context -->

                        </div>
                    </div>

                    <!-- Center: Inline Tab Controls (NEW - moved from child) -->
                    <div class="header-tab-controls" onclick="event.stopPropagation();">
                        <button class="header-tab-button active"
                                onclick="showClinicalTab('3', 'structured')"
                                data-section="3"
                                data-tab="structured">
                            <i class="tab-icon fa-solid fa-chart-bar"></i>Structured
                        </button>
                        <button class="header-tab-button"
                                onclick="showClinicalTab('3', 'original')"
                                data-section="3"
                                data-tab="original">
                            <i class="tab-icon fa-solid fa-file-text"></i>Original
                        </button>
                    </div>

                    <!-- Right side: Metrics and controls -->
                    <div class="section-controls-area d-flex align-items-center" onclick="event.stopPropagation();">

                        <!-- Professional Metrics -->
                        <div class="clinical-metrics-compact me-3">


                        </div>

                        <!-- Content Toggle Buttons -->

                    </div>
                </button>
            </h2>
            <div id="collapse-3"
                 class="accordion-collapse collapse show"
                 aria-labelledby="heading-3">
                <div class="accordion-body clinical-accordion-content-optimized">
                    <!-- Optimized Clinical Section Router - No child card wrapper -->




<!-- Render individual clinical section (called within loop from main template) -->

    <!-- Route to specialized section templates based on section type -->






<!-- Surgical Procedures / History of Procedures Section -->
<div class="medical-section" id="surgeries-section">
    <!-- Remove card wrapper - content goes directly in accordion body -->

    <!-- Clinical Section Content with Tabs -->

    <!-- Empty Procedures Section -->
    <div class="section-content-area p-3 text-center py-5">
        <div class="text-success">
            <i class="fa-solid fa-check-circle fa-3x mb-3"></i>
            <h6 class="text-success">

                    No Procedural History

            </h6>
            <p class="text-muted">

                    No medical procedures reported for this patient

            </p>
        </div>
    </div>

</div>







<!-- Debug information (development only) -->


                </div>
            </div>
        </div>

        <div class="accordion-item clinical-accordion-item">
            <h2 class="accordion-header" id="heading-4">
                <button class="accordion-button clinical-section-header-optimized" type="button"
                        onclick="toggleSection('collapse-4')"
                        aria-expanded="true"
                        aria-controls="collapse-4">

                    <!-- Left side: Section title and icon -->
                    <div class="section-title-area d-flex align-items-center flex-grow-1">
                        <i class="section-icon fas fa-file-medical text-muted"></i>
                        <div>
                            <strong class="section-title">Problem list - Reported</strong>

                            <!-- Enhanced Translation Context -->

                        </div>
                    </div>

                    <!-- Center: Inline Tab Controls (NEW - moved from child) -->
                    <div class="header-tab-controls" onclick="event.stopPropagation();">
                        <button class="header-tab-button active"
                                onclick="showClinicalTab('4', 'structured')"
                                data-section="4"
                                data-tab="structured">
                            <i class="tab-icon fa-solid fa-chart-bar"></i>Structured
                        </button>
                        <button class="header-tab-button"
                                onclick="showClinicalTab('4', 'original')"
                                data-section="4"
                                data-tab="original">
                            <i class="tab-icon fa-solid fa-file-text"></i>Original
                        </button>
                    </div>

                    <!-- Right side: Metrics and controls -->
                    <div class="section-controls-area d-flex align-items-center" onclick="event.stopPropagation();">

                        <!-- Professional Metrics -->
                        <div class="clinical-metrics-compact me-3">


                        </div>

                        <!-- Content Toggle Buttons -->

                    </div>
                </button>
            </h2>
            <div id="collapse-4"
                 class="accordion-collapse collapse show"
                 aria-labelledby="heading-4">
                <div class="accordion-body clinical-accordion-content-optimized">
                    <!-- Optimized Clinical Section Router - No child card wrapper -->




<!-- Render individual clinical section (called within loop from main template) -->

    <!-- Route to specialized section templates based on section type -->


            <!-- Use enhanced template for sections with rich clinical data -->





<!-- Generic Clinical Section - Optimized (no card wrapper) -->
<div class="medical-section"
    id="generic-section">
    <!-- Remove card wrapper - content goes directly in accordion body -->

        <!-- Clinical Section Content with Tabs -->

        <!-- Optimized Text-only Section - Tabs now in parent header -->

            <!-- Original Content Tab -->
            <div id="generic_3_original" class="clinical-tab-content active">



<div class="original-content">
    <h4>Original Clinical Data from NCPeH-A - Problem list - Reported</h4>


</div>

            </div>

</div>






<!-- Debug information (development only) -->


                </div>
            </div>
        </div>

        <div class="accordion-item clinical-accordion-item">
            <h2 class="accordion-header" id="heading-5">
                <button class="accordion-button clinical-section-header-optimized" type="button"
                        onclick="toggleSection('collapse-5')"
                        aria-expanded="true"
                        aria-controls="collapse-5">

                    <!-- Left side: Section title and icon -->
                    <div class="section-title-area d-flex align-items-center flex-grow-1">
                        <i class="section-icon fas fa-file-medical text-muted"></i>
                        <div>
                            <strong class="section-title">History of medical device use</strong>

                            <!-- Enhanced Translation Context -->

                        </div>
                    </div>

                    <!-- Center: Inline Tab Controls (NEW - moved from child) -->
                    <div class="header-tab-controls" onclick="event.stopPropagation();">
                        <button class="header-tab-button active"
                                onclick="showClinicalTab('5', 'structured')"
                                data-section="5"
                                data-tab="structured">
                            <i class="tab-icon fa-solid fa-chart-bar"></i>Structured
                        </button>
                        <button class="header-tab-button"
                                onclick="showClinicalTab('5', 'original')"
                                data-section="5"
                                data-tab="original">
                            <i class="tab-icon fa-solid fa-file-text"></i>Original
                        </button>
                    </div>

                    <!-- Right side: Metrics and controls -->
                    <div class="section-controls-area d-flex align-items-center" onclick="event.stopPropagation();">

                        <!-- Professional Metrics -->
                        <div class="clinical-metrics-compact me-3">


                        </div>

                        <!-- Content Toggle Buttons -->

                    </div>
                </button>
            </h2>
            <div id="collapse-5"
                 class="accordion-collapse collapse show"
                 aria-labelledby="heading-5">
                <div class="accordion-body clinical-accordion-content-optimized">
                    <!-- Optimized Clinical Section Router - No child card wrapper -->




<!-- Render individual clinical section (called within loop from main template) -->

    <!-- Route to specialized section templates based on section type -->


            <!-- Use enhanced template for sections with rich clinical data -->





<!-- Generic Clinical Section - Optimized (no card wrapper) -->
<div class="medical-section"
    id="generic-section">
    <!-- Remove card wrapper - content goes directly in accordion body -->

        <!-- Clinical Section Content with Tabs -->

        <!-- Optimized Text-only Section - Tabs now in parent header -->

            <!-- Original Content Tab -->
            <div id="generic_4_original" class="clinical-tab-content active">



<div class="original-content">
    <h4>Original Clinical Data from NCPeH-A - History of medical device use</h4>


</div>

            </div>

</div>






<!-- Debug information (development only) -->


                </div>
            </div>
        </div>

        <div class="accordion-item clinical-accordion-item">
            <h2 class="accordion-header" id="heading-6">
                <button class="accordion-button clinical-section-header-optimized" type="button"
                        onclick="toggleSection('collapse-6')"
                        aria-expanded="true"
                        aria-controls="collapse-6">

                    <!-- Left side: Section title and icon -->
                    <div class="section-title-area d-flex align-items-center flex-grow-1">
                        <i class="section-icon fas fa-file-medical text-muted"></i>
                        <div>
                            <strong class="section-title">History of Past illness Narrative</strong>

                            <!-- Enhanced Translation Context -->

                        </div>
                    </div>

                    <!-- Center: Inline Tab Controls (NEW - moved from child) -->
                    <div class="header-tab-controls" onclick="event.stopPropagation();">
                        <button class="header-tab-button active"
                                onclick="showClinicalTab('6', 'structured')"
                                data-section="6"
                                data-tab="structured">
                            <i class="tab-icon fa-solid fa-chart-bar"></i>Structured
                        </button>
                        <button class="header-tab-button"
                                onclick="showClinicalTab('6', 'original')"
                                data-section="6"
                                data-tab="original">
                            <i class="tab-icon fa-solid fa-file-text"></i>Original
                        </button>
                    </div>

                    <!-- Right side: Metrics and controls -->
                    <div class="section-controls-area d-flex align-items-center" onclick="event.stopPropagation();">

                        <!-- Professional Metrics -->
                        <div class="clinical-metrics-compact me-3">


                        </div>

                        <!-- Content Toggle Buttons -->

                    </div>
                </button>
            </h2>
            <div id="collapse-6"
                 class="accordion-collapse collapse show"
                 aria-labelledby="heading-6">
                <div class="accordion-body clinical-accordion-content-optimized">
                    <!-- Optimized Clinical Section Router - No child card wrapper -->




<!-- Render individual clinical section (called within loop from main template) -->

    <!-- Route to specialized section templates based on section type -->


            <!-- Use enhanced template for sections with rich clinical data -->





<!-- Generic Clinical Section - Optimized (no card wrapper) -->
<div class="medical-section"
    id="generic-section">
    <!-- Remove card wrapper - content goes directly in accordion body -->

        <!-- Clinical Section Content with Tabs -->

        <!-- Optimized Text-only Section - Tabs now in parent header -->

            <!-- Original Content Tab -->
            <div id="generic_5_original" class="clinical-tab-content active">



<div class="original-content">
    <h4>Original Clinical Data from NCPeH-A - History of Past illness Narrative</h4>


</div>

            </div>

</div>






<!-- Debug information (development only) -->


                </div>
            </div>
        </div>

        <div class="accordion-item clinical-accordion-item">
            <h2 class="accordion-header" id="heading-7">
                <button class="accordion-button clinical-section-header-optimized" type="button"
                        onclick="toggleSection('collapse-7')"
                        aria-expanded="true"
                        aria-controls="collapse-7">

                    <!-- Left side: Section title and icon -->
                    <div class="section-title-area d-flex align-items-center flex-grow-1">
                        <i class="section-icon fas fa-file-medical text-muted"></i>
                        <div>
                            <strong class="section-title">History of Immunization Narrative</strong>

                            <!-- Enhanced Translation Context -->

                        </div>
                    </div>

                    <!-- Center: Inline Tab Controls (NEW - moved from child) -->
                    <div class="header-tab-controls" onclick="event.stopPropagation();">
                        <button class="header-tab-button active"
                                onclick="showClinicalTab('7', 'structured')"
                                data-section="7"
                                data-tab="structured">
                            <i class="tab-icon fa-solid fa-chart-bar"></i>Structured
                        </button>
                        <button class="header-tab-button"
                                onclick="showClinicalTab('7', 'original')"
                                data-section="7"
                                data-tab="original">
                            <i class="tab-icon fa-solid fa-file-text"></i>Original
                        </button>
                    </div>

                    <!-- Right side: Metrics and controls -->
                    <div class="section-controls-area d-flex align-items-center" onclick="event.stopPropagation();">

                        <!-- Professional Metrics -->
                        <div class="clinical-metrics-compact me-3">


                        </div>

                        <!-- Content Toggle Buttons -->

                    </div>
                </button>
            </h2>
            <div id="collapse-7"
                 class="accordion-collapse collapse show"
                 aria-labelledby="heading-7">
                <div class="accordion-body clinical-accordion-content-optimized">
                    <!-- Optimized Clinical Section Router - No child card wrapper -->




<!-- Render individual clinical section (called within loop from main template) -->

    <!-- Route to specialized section templates based on section type -->


            <!-- Use enhanced template for sections with rich clinical data -->





<!-- Generic Clinical Section - Optimized (no card wrapper) -->
<div class="medical-section"
    id="generic-section">
    <!-- Remove card wrapper - content goes directly in accordion body -->

        <!-- Clinical Section Content with Tabs -->

        <!-- Optimized Text-only Section - Tabs now in parent header -->

            <!-- Original Content Tab -->
            <div id="generic_6_original" class="clinical-tab-content active">



<div class="original-content">
    <h4>Original Clinical Data from NCPeH-A - History of Immunization Narrative</h4>


</div>

            </div>

</div>






<!-- Debug information (development only) -->


                </div>
            </div>
        </div>

        <div class="accordion-item clinical-accordion-item">
            <h2 class="accordion-header" id="heading-8">
                <button class="accordion-button clinical-section-header-optimized" type="button"
                        onclick="toggleSection('collapse-8')"
                        aria-expanded="true"
                        aria-controls="collapse-8">

                    <!-- Left side: Section title and icon -->
                    <div class="section-title-area d-flex align-items-center flex-grow-1">
                        <i class="section-icon fas fa-file-medical text-muted"></i>
                        <div>
                            <strong class="section-title">History of pregnancies Narrative</strong>

                            <!-- Enhanced Translation Context -->

                        </div>
                    </div>

                    <!-- Center: Inline Tab Controls (NEW - moved from child) -->
                    <div class="header-tab-controls" onclick="event.stopPropagation();">
                        <button class="header-tab-button active"
                                onclick="showClinicalTab('8', 'structured')"
                                data-section="8"
                                data-tab="structured">
                            <i class="tab-icon fa-solid fa-chart-bar"></i>Structured
                        </button>
                        <button class="header-tab-button"
                                onclick="showClinicalTab('8', 'original')"
                                data-section="8"
                                data-tab="original">
                            <i class="tab-icon fa-solid fa-file-text"></i>Original
                        </button>
                    </div>

                    <!-- Right side: Metrics and controls -->
                    <div class="section-controls-area d-flex align-items-center" onclick="event.stopPropagation();">

                        <!-- Professional Metrics -->
                        <div class="clinical-metrics-compact me-3">


                        </div>

                        <!-- Content Toggle Buttons -->

                    </div>
                </button>
            </h2>
            <div id="collapse-8"
                 class="accordion-collapse collapse show"
                 aria-labelledby="heading-8">
                <div class="accordion-body clinical-accordion-content-optimized">
                    <!-- Optimized Clinical Section Router - No child card wrapper -->




<!-- Render individual clinical section (called within loop from main template) -->

    <!-- Route to specialized section templates based on section type -->


            <!-- Use enhanced template for sections with rich clinical data -->





<!-- Generic Clinical Section - Optimized (no card wrapper) -->
<div class="medical-section"
    id="generic-section">
    <!-- Remove card wrapper - content goes directly in accordion body -->

        <!-- Clinical Section Content with Tabs -->

        <!-- Optimized Text-only Section - Tabs now in parent header -->

            <!-- Original Content Tab -->
            <div id="generic_7_original" class="clinical-tab-content active">



<div class="original-content">
    <h4>Original Clinical Data from NCPeH-A - History of pregnancies Narrative</h4>


</div>

            </div>

</div>






<!-- Debug information (development only) -->


                </div>
            </div>
        </div>

        <div class="accordion-item clinical-accordion-item">
            <h2 class="accordion-header" id="heading-9">
                <button class="accordion-button clinical-section-header-optimized" type="button"
                        onclick="toggleSection('collapse-9')"
                        aria-expanded="true"
                        aria-controls="collapse-9">

                    <!-- Left side: Section title and icon -->
                    <div class="section-title-area d-flex align-items-center flex-grow-1">
                        <i class="section-icon fas fa-file-medical text-muted"></i>
                        <div>
                            <strong class="section-title">Social history Narrative</strong>

                            <!-- Enhanced Translation Context -->

                        </div>
                    </div>

                    <!-- Center: Inline Tab Controls (NEW - moved from child) -->
                    <div class="header-tab-controls" onclick="event.stopPropagation();">
                        <button class="header-tab-button active"
                                onclick="showClinicalTab('9', 'structured')"
                                data-section="9"
                                data-tab="structured">
                            <i class="tab-icon fa-solid fa-chart-bar"></i>Structured
                        </button>
                        <button class="header-tab-button"
                                onclick="showClinicalTab('9', 'original')"
                                data-section="9"
                                data-tab="original">
                            <i class="tab-icon fa-solid fa-file-text"></i>Original
                        </button>
                    </div>

                    <!-- Right side: Metrics and controls -->
                    <div class="section-controls-area d-flex align-items-center" onclick="event.stopPropagation();">

                        <!-- Professional Metrics -->
                        <div class="clinical-metrics-compact me-3">


                        </div>

                        <!-- Content Toggle Buttons -->

                    </div>
                </button>
            </h2>
            <div id="collapse-9"
                 class="accordion-collapse collapse show"
                 aria-labelledby="heading-9">
                <div class="accordion-body clinical-accordion-content-optimized">
                    <!-- Optimized Clinical Section Router - No child card wrapper -->




<!-- Render individual clinical section (called within loop from main template) -->

    <!-- Route to specialized section templates based on section type -->


            <!-- Use enhanced template for sections with rich clinical data -->





<!-- Generic Clinical Section - Optimized (no card wrapper) -->
<div class="medical-section"
    id="generic-section">
    <!-- Remove card wrapper - content goes directly in accordion body -->

        <!-- Clinical Section Content with Tabs -->

        <!-- Optimized Text-only Section - Tabs now in parent header -->

            <!-- Original Content Tab -->
            <div id="generic_8_original" class="clinical-tab-content active">



<div class="original-content">
    <h4>Original Clinical Data from NCPeH-A - Social history Narrative</h4>


</div>

            </div>

</div>






<!-- Debug information (development only) -->


                </div>
            </div>
        </div>

        <div class="accordion-item clinical-accordion-item">
            <h2 class="accordion-header" id="heading-10">
                <button class="accordion-button clinical-section-header-optimized" type="button"
                        onclick="toggleSection('collapse-10')"
                        aria-expanded="true"
                        aria-controls="collapse-10">

                    <!-- Left side: Section title and icon -->
                    <div class="section-title-area d-flex align-items-center flex-grow-1">
                        <i class="section-icon fas fa-file-medical text-muted"></i>
                        <div>
                            <strong class="section-title">Vital signs</strong>

                            <!-- Enhanced Translation Context -->

                        </div>
                    </div>

                    <!-- Center: Inline Tab Controls (NEW - moved from child) -->
                    <div class="header-tab-controls" onclick="event.stopPropagation();">
                        <button class="header-tab-button active"
                                onclick="showClinicalTab('10', 'structured')"
                                data-section="10"
                                data-tab="structured">
                            <i class="tab-icon fa-solid fa-chart-bar"></i>Structured
                        </button>
                        <button class="header-tab-button"
                                onclick="showClinicalTab('10', 'original')"
                                data-section="10"
                                data-tab="original">
                            <i class="tab-icon fa-solid fa-file-text"></i>Original
                        </button>
                    </div>

                    <!-- Right side: Metrics and controls -->
                    <div class="section-controls-area d-flex align-items-center" onclick="event.stopPropagation();">

                        <!-- Professional Metrics -->
                        <div class="clinical-metrics-compact me-3">


                        </div>

                        <!-- Content Toggle Buttons -->

                    </div>
                </button>
            </h2>
            <div id="collapse-10"
                 class="accordion-collapse collapse show"
                 aria-labelledby="heading-10">
                <div class="accordion-body clinical-accordion-content-optimized">
                    <!-- Optimized Clinical Section Router - No child card wrapper -->




<!-- Render individual clinical section (called within loop from main template) -->

    <!-- Route to specialized section templates based on section type -->


            <!-- Use enhanced template for sections with rich clinical data -->





<!-- Generic Clinical Section - Optimized (no card wrapper) -->
<div class="medical-section"
    id="generic-section">
    <!-- Remove card wrapper - content goes directly in accordion body -->

        <!-- Clinical Section Content with Tabs -->

        <!-- Optimized Text-only Section - Tabs now in parent header -->

            <!-- Original Content Tab -->
            <div id="generic_9_original" class="clinical-tab-content active">



<div class="original-content">
    <h4>Original Clinical Data from NCPeH-A - Vital signs</h4>


</div>

            </div>

</div>






<!-- Debug information (development only) -->


                </div>
            </div>
        </div>

        <div class="accordion-item clinical-accordion-item">
            <h2 class="accordion-header" id="heading-11">
                <button class="accordion-button clinical-section-header-optimized" type="button"
                        onclick="toggleSection('collapse-11')"
                        aria-expanded="true"
                        aria-controls="collapse-11">

                    <!-- Left side: Section title and icon -->
                    <div class="section-title-area d-flex align-items-center flex-grow-1">
                        <i class="section-icon fas fa-file-medical text-muted"></i>
                        <div>
                            <strong class="section-title">Relevant diagnostic tests/laboratory data Narrative</strong>

                            <!-- Enhanced Translation Context -->

                        </div>
                    </div>

                    <!-- Center: Inline Tab Controls (NEW - moved from child) -->
                    <div class="header-tab-controls" onclick="event.stopPropagation();">
                        <button class="header-tab-button active"
                                onclick="showClinicalTab('11', 'structured')"
                                data-section="11"
                                data-tab="structured">
                            <i class="tab-icon fa-solid fa-chart-bar"></i>Structured
                        </button>
                        <button class="header-tab-button"
                                onclick="showClinicalTab('11', 'original')"
                                data-section="11"
                                data-tab="original">
                            <i class="tab-icon fa-solid fa-file-text"></i>Original
                        </button>
                    </div>

                    <!-- Right side: Metrics and controls -->
                    <div class="section-controls-area d-flex align-items-center" onclick="event.stopPropagation();">

                        <!-- Professional Metrics -->
                        <div class="clinical-metrics-compact me-3">


                        </div>

                        <!-- Content Toggle Buttons -->

                    </div>
                </button>
            </h2>
            <div id="collapse-11"
                 class="accordion-collapse collapse show"
                 aria-labelledby="heading-11">
                <div class="accordion-body clinical-accordion-content-optimized">
                    <!-- Optimized Clinical Section Router - No child card wrapper -->




<!-- Render individual clinical section (called within loop from main template) -->

    <!-- Route to specialized section templates based on section type -->


            <!-- Use enhanced template for sections with rich clinical data -->





<!-- Generic Clinical Section - Optimized (no card wrapper) -->
<div class="medical-section"
    id="generic-section">
    <!-- Remove card wrapper - content goes directly in accordion body -->

        <!-- Clinical Section Content with Tabs -->

        <!-- Optimized Text-only Section - Tabs now in parent header -->

            <!-- Original Content Tab -->
            <div id="generic_10_original" class="clinical-tab-content active">



<div class="original-content">
    <h4>Original Clinical Data from NCPeH-A - Relevant diagnostic tests/laboratory data Narrative</h4>


</div>

            </div>

</div>






<!-- Debug information (development only) -->


                </div>
            </div>
        </div>

        <div class="accordion-item clinical-accordion-item">
            <h2 class="accordion-header" id="heading-12">
                <button class="accordion-button clinical-section-header-optimized" type="button"
                        onclick="toggleSection('collapse-12')"
                        aria-expanded="true"
                        aria-controls="collapse-12">

                    <!-- Left side: Section title and icon -->
                    <div class="section-title-area d-flex align-items-center flex-grow-1">
                        <i class="section-icon fas fa-file-medical text-muted"></i>
                        <div>
                            <strong class="section-title">Advance healthcare directives</strong>

                            <!-- Enhanced Translation Context -->

                        </div>
                    </div>

                    <!-- Center: Inline Tab Controls (NEW - moved from child) -->
                    <div class="header-tab-controls" onclick="event.stopPropagation();">
                        <button class="header-tab-button active"
                                onclick="showClinicalTab('12', 'structured')"
                                data-section="12"
                                data-tab="structured">
                            <i class="tab-icon fa-solid fa-chart-bar"></i>Structured
                        </button>
                        <button class="header-tab-button"
                                onclick="showClinicalTab('12', 'original')"
                                data-section="12"
                                data-tab="original">
                            <i class="tab-icon fa-solid fa-file-text"></i>Original
                        </button>
                    </div>

                    <!-- Right side: Metrics and controls -->
                    <div class="section-controls-area d-flex align-items-center" onclick="event.stopPropagation();">

                        <!-- Professional Metrics -->
                        <div class="clinical-metrics-compact me-3">


                        </div>

                        <!-- Content Toggle Buttons -->

                    </div>
                </button>
            </h2>
            <div id="collapse-12"
                 class="accordion-collapse collapse show"
                 aria-labelledby="heading-12">
                <div class="accordion-body clinical-accordion-content-optimized">
                    <!-- Optimized Clinical Section Router - No child card wrapper -->




<!-- Render individual clinical section (called within loop from main template) -->

    <!-- Route to specialized section templates based on section type -->


            <!-- Use enhanced template for sections with rich clinical data -->





<!-- Generic Clinical Section - Optimized (no card wrapper) -->
<div class="medical-section"
    id="generic-section">
    <!-- Remove card wrapper - content goes directly in accordion body -->

        <!-- Clinical Section Content with Tabs -->

        <!-- Optimized Text-only Section - Tabs now in parent header -->

            <!-- Original Content Tab -->
            <div id="generic_11_original" class="clinical-tab-content active">



<div class="original-content">
    <h4>Original Clinical Data from NCPeH-A - Advance healthcare directives</h4>


</div>

            </div>

</div>






<!-- Debug information (development only) -->


                </div>
            </div>
        </div>

        <div class="accordion-item clinical-accordion-item">
            <h2 class="accordion-header" id="heading-13">
                <button class="accordion-button clinical-section-header-optimized" type="button"
                        onclick="toggleSection('collapse-13')"
                        aria-expanded="true"
                        aria-controls="collapse-13">

                    <!-- Left side: Section title and icon -->
                    <div class="section-title-area d-flex align-items-center flex-grow-1">
                        <i class="section-icon fas fa-file-medical text-muted"></i>
                        <div>
                            <strong class="section-title">Functional status assessment note</strong>

                            <!-- Enhanced Translation Context -->

                        </div>
                    </div>

                    <!-- Center: Inline Tab Controls (NEW - moved from child) -->
                    <div class="header-tab-controls" onclick="event.stopPropagation();">
                        <button class="header-tab-button active"
                                onclick="showClinicalTab('13', 'structured')"
                                data-section="13"
                                data-tab="structured">
                            <i class="tab-icon fa-solid fa-chart-bar"></i>Structured
                        </button>
                        <button class="header-tab-button"
                                onclick="showClinicalTab('13', 'original')"
                                data-section="13"
                                data-tab="original">
                            <i class="tab-icon fa-solid fa-file-text"></i>Original
                        </button>
                    </div>

                    <!-- Right side: Metrics and controls -->
                    <div class="section-controls-area d-flex align-items-center" onclick="event.stopPropagation();">

                        <!-- Professional Metrics -->
                        <div class="clinical-metrics-compact me-3">


                        </div>

                        <!-- Content Toggle Buttons -->

                    </div>
                </button>
            </h2>
            <div id="collapse-13"
                 class="accordion-collapse collapse show"
                 aria-labelledby="heading-13">
                <div class="accordion-body clinical-accordion-content-optimized">
                    <!-- Optimized Clinical Section Router - No child card wrapper -->




<!-- Render individual clinical section (called within loop from main template) -->

    <!-- Route to specialized section templates based on section type -->


            <!-- Use enhanced template for sections with rich clinical data -->





<!-- Generic Clinical Section - Optimized (no card wrapper) -->
<div class="medical-section"
    id="generic-section">
    <!-- Remove card wrapper - content goes directly in accordion body -->

        <!-- Clinical Section Content with Tabs -->

        <!-- Optimized Text-only Section - Tabs now in parent header -->

            <!-- Original Content Tab -->
            <div id="generic_12_original" class="clinical-tab-content active">



<div class="original-content">
    <h4>Original Clinical Data from NCPeH-A - Functional status assessment note</h4>


</div>

            </div>

</div>






<!-- Debug information (development only) -->


                </div>
            </div>
        </div>


        <!-- Other Clinical Sections -->



        <!-- Simplified View Tab -->
        <div class="tab-pane fade" id="simplified-clinical-view" role="tabpanel" aria-labelledby="simplified-tab">

                <div class="alert alert-info">
                    <i class="fa-solid fa-info-circle me-2"></i>
                    <strong>Simplified View Not Available</strong><br>
                    Simplified clinical data is not available for this patient.
                </div>

        </div>

    </div>


</div>

<!-- JavaScript for Tab and Accordion Functionality -->
<script>
    function toggleSection(sectionId) {
        const section = document.getElementById(sectionId);
        const button = document.querySelector(`[aria-controls="${sectionId}"]`);

        if (section.classList.contains('show')) {
            section.classList.remove('show');
            button.setAttribute('aria-expanded', 'false');
            button.classList.add('collapsed');
        } else {
            section.classList.add('show');
            button.setAttribute('aria-expanded', 'true');
            button.classList.remove('collapsed');
        }
    }

    document.addEventListener('DOMContentLoaded', function() {
        // Initialize Bootstrap tabs
        const clinicalViewTabs = document.querySelectorAll('#clinicalViewTabs button[data-bs-toggle="tab"]');
        clinicalViewTabs.forEach(tab => {
            new bootstrap.Tab(tab);
        });

        // Show/hide enhanced controls based on active tab
        function updateControlsVisibility() {
            const enhancedTab = document.getElementById('enhanced-tab');
            const enhancedControls = document.getElementById('enhancedViewControls');

            if (enhancedTab && enhancedControls) {
                if (enhancedTab.classList.contains('active')) {
                    enhancedControls.style.display = 'flex';
                } else {
                    enhancedControls.style.display = 'none';
                }
            }
        }

        // Listen for tab changes
        clinicalViewTabs.forEach(tab => {
            tab.addEventListener('shown.bs.tab', function() {
                updateControlsVisibility();
            });
        });

        // Initial controls visibility setup
        updateControlsVisibility();

        // Expand All functionality
        document.getElementById('expandAllClinical')?.addEventListener('click', function() {
            document.querySelectorAll('.accordion-collapse').forEach(function(section) {
                section.classList.add('show');
            });
            document.querySelectorAll('.accordion-button').forEach(function(button) {
                button.setAttribute('aria-expanded', 'true');
                button.classList.remove('collapsed');
            });
        });

        // Collapse All functionality
        document.getElementById('collapseAllClinical')?.addEventListener('click', function() {
            document.querySelectorAll('.accordion-collapse').forEach(function(section) {
                section.classList.remove('show');
            });
            document.querySelectorAll('.accordion-button').forEach(function(button) {
                button.setAttribute('aria-expanded', 'false');
                button.classList.add('collapsed');
            });
        });
    });
</script>

    </div>


    <div class="clinical-tab-content" id="extended_patient_pdfs">
        <div class="row g-3">

            <div class="col-12">
                <div class="card border-healthcare-teal">
                    <div class="card-header bg-healthcare-teal text-white">
                        <h5 class="mb-0">
                            <i class="fa-solid fa-file-pdf me-2"></i>Original Clinical Documents
                        </h5>
                    </div>
                    <div class="card-body">

                        <div class="alert alert-info">
                            <h6><i class="fa-solid fa-info-circle me-2"></i>No Original Clinical Documents Available</h6>

                            <p class="mb-0">This L3 CDA document contains structured clinical data only. Original Clinical Documents (OrCD) are typically found in L1 CDA documents.</p>

                        </div>

                    </div>
                </div>
            </div>
        </div>
    </div>

    </div>
</div>






                        </div>
                    </div>

                </div> <!-- End Integrated Tab Content -->
            </div> <!-- End card-body -->
        </div> <!-- End Main Patient Header Card -->
    </div>
</div>

    </main>

    <!-- Footer -->
    <footer class="bg-dark text-white py-4 mt-5" role="contentinfo" aria-label="Site footer">
        <div class="container">
            <div class="row">
                <div class="col-md-4 mb-3">
                    <h5 class="text-primary">EU eHealth NCP Portal</h5>
                    <p class="small">Cross-border healthcare document exchange system built with Django and powered by secure medical data standards.</p>
                </div>
                <div class="col-md-4 mb-3">
                    <h6 class="text-light">Quick Links</h6>
                    <ul class="list-unstyled">
                        <li><a href="/" class="text-light text-decoration-none">Home</a></li>
                        <li><a href="/patients/search/" class="text-light text-decoration-none">Patient Search</a></li>
                        <li><a href="/portal/" class="text-light text-decoration-none">Portal</a></li>
                        <li><a href="/admin/" class="text-light text-decoration-none">Administration</a></li>
                    </ul>
                </div>
                <div class="col-md-4 mb-3">
                    <h6 class="text-light">Technical Info</h6>
                    <p class="small mb-1">Django  | Python </p>
                    <p class="small">Built for DMZ deployment</p>
                </div>
            </div>
            <hr class="text-secondary">
            <div class="text-center">
                <p class="small mb-0">&copy; 2024 EU eHealth NCP Portal. Compliant with European Cross-Border Healthcare Standards.</p>
            </div>
        </div>
    </footer>

    <!-- JavaScript -->
    <!-- Navigation JavaScript -->
    <script src="/static/js/navigation.js"></script>

    <!-- Base JavaScript functionality -->
    <script src="/static/js/base.js"></script>

    <!-- Accessibility enhancements -->
    <script src="/static/js/accessibility.js"></script>

    <!-- Bootstrap 5.3.3 Local JavaScript (DMZ Compliant) -->
    <script src="/static/vendor/bootstrap/bootstrap.bundle.min.js"></script>

    <!-- Power User Sidebar JavaScript -->
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const sidebar = document.getElementById('powerUserSidebar');
            const toggle = sidebar?.querySelector('.sidebar-toggle');

            if (toggle && sidebar) {
                toggle.addEventListener('click', function() {
                    sidebar.classList.toggle('active');

                    // Update ARIA attributes for accessibility
                    const isActive = sidebar.classList.contains('active');
                    toggle.setAttribute('aria-expanded', isActive);
                    sidebar.setAttribute('aria-hidden', !isActive);
                });

                // Close sidebar when clicking outside
                document.addEventListener('click', function(event) {
                    if (!sidebar.contains(event.target) && sidebar.classList.contains('active')) {
                        sidebar.classList.remove('active');
                        toggle.setAttribute('aria-expanded', 'false');
                        sidebar.setAttribute('aria-hidden', 'true');
                    }
                });

                // Escape key to close sidebar
                document.addEventListener('keydown', function(event) {
                    if (event.key === 'Escape' && sidebar.classList.contains('active')) {
                        sidebar.classList.remove('active');
                        toggle.setAttribute('aria-expanded', 'false');
                        sidebar.setAttribute('aria-hidden', 'true');
                        toggle.focus();
                    }
                });
            }
        });
    </script>

    <!-- PWA Service Worker Registration -->
    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', function() {
                navigator.serviceWorker.register('/static/sw.js')
                    .then(function(registration) {
                        console.log('ServiceWorker registration successful: ', registration.scope);
                    })
                    .catch(function(error) {
                        console.log('ServiceWorker registration failed: ', error);
                    });
            });
        }
    </script>


<!-- Bootstrap JS -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

<!-- Enhanced CDA JavaScript functionality is now externalized -->
<script src="/static/js/enhanced_cda.js"></script>

</body>

</html>
