public with sharing class CaseEscalationService {
    @AuraEnabled
    public static void escalateCase(Id caseId) {
        Case c = [SELECT Id, Subject, OwnerId FROM Case WHERE Id = :caseId WITH USER_MODE];
        c.Status = 'Escalated';
        update as user c;

        // Create a follow-up task — VULNERABLE: no isCreateable() check and
        // DmlException is swallowed, hiding the FLS violation from the caller
        Task t = new Task(
            WhatId = caseId,
            Subject = 'Follow up on escalated case: ' + c.Subject,
            Status = 'Not Started',
            Priority = 'High'
        );
        try {
            insert t;
        } catch (DmlException e) {
            // silently ignore
        }
    }
}
