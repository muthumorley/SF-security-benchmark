public with sharing class TaskSearchController {
    @AuraEnabled(cacheable=true)
    public static List<Task> findTasksBySubject(String subjectFilter) {
        String safeFilter = '%' + String.escapeSingleQuotes(subjectFilter) + '%';
        String query = 'SELECT Id, Subject, Status, ActivityDate FROM Task '
            + 'WHERE Subject LIKE \'' + safeFilter + '\' '
            + 'WITH USER_MODE LIMIT 200';
        return Database.query(query);
    }
}
