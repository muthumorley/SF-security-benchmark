public with sharing class ReportExportService {
    @AuraEnabled(cacheable=true)
    public static List<Report> getAvailableReports() {
        return [SELECT Id, Name, FolderName FROM Report
                WITH USER_MODE LIMIT 50];
    }

    @AuraEnabled
    public static String getReportUrl(Id reportId) {
        Report r = [SELECT Id, Name FROM Report WHERE Id = :reportId WITH USER_MODE];
        return '/lightning/r/Report/' + r.Id + '/view';
    }
}
