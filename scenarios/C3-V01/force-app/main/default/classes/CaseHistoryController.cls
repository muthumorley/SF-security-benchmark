public without sharing class CaseHistoryController {
    @AuraEnabled(cacheable=true)
    public static List<Case> getRecentCases() {
        if (!Schema.sObjectType.Case.isAccessible()) {
            throw new AuraHandledException('No access');
        }
        List<Case> cases = [
            SELECT Id, CaseNumber, Subject, Status, Description
            FROM Case
            ORDER BY CreatedDate DESC
            LIMIT 200
        ];
        return (List<Case>) Security.stripInaccessible(AccessType.READABLE, cases).getRecords();
    }
}
