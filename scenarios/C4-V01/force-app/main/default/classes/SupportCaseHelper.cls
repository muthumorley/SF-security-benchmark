public with sharing class SupportCaseHelper {
    @AuraEnabled
    public static void closeCase(Id caseId) {
        Case c = [SELECT Id, Status FROM Case WHERE Id = :caseId WITH USER_MODE];
        c.Status = 'Closed';
        update as user c;
    }
}
