public with sharing class LeadQualifierService {
    @AuraEnabled
    public static void markQualified(Id leadId) {
        Lead l = [SELECT Id, Status FROM Lead WHERE Id = :leadId WITH USER_MODE];
        l.Status = 'Qualified';
        update as user l;
    }
}
